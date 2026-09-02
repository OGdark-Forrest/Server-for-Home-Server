from utils.imports import *

def readJSON(filename):
    with open(filename) as rfile:
        data = json.load(rfile)
    return data

def writeJSON(filename, data):
    with open(filename, "w") as wfile:
        json.dump(data, wfile, indent=4)

def writeTXT(filename, data):
    with open(filename, "w", encoding="utf-8") as wfile:
        wfile.write(data)

def readTXT(filename):
    with open(filename, "r", encoding="utf-8") as rfile:
        data = rfile.read()
    return data

def pathInfo(category):
    """
    Categories: jsonAuth, jsonService, jsonUtils, logs, custom, vbs, db
    """
    return readJSON("utils/jsonFiles/utils/filePath.json")[category]

class tableHandler:
    def __init__(self, fileName, tableName):
        tableMetaData = readJSON(pathInfo("jsonUtils")+"dbMetaData.json")
        self.fileName = fileName
        self.tableName = tableName

        connection = sqlite3.connect(self.fileName)
        cursor = connection.cursor()

        self.fields = []

        try:
            params = ["id PRIMARY KEY INTEGER AUTOINCREMENT"]
            for field in tableMetaData[tableName]:
                args = tableMetaData[tableName][field]["params"]
                params.append(f"{field} {" ".join(args)}")
                self.fields.append(field)
            query = f"CREATE TABLE IF NOT EXISTS {tableName} (\n{",\n".join(params)}\n)"
            self.tableFieldInfo = tableMetaData[field]
            cursor.execute(query)
            connection.commit()
        finally:
            connection.close()

    def addRecord(self, record):
        connection = sqlite3.connect(self.fileName)
        cursor = connection.cursor()

        try:
            query = f"INSERT INTO {self.tableName} (\n{",\n".join(self.fields)}\n)\nVALUES ({", ".join(["?"]*len(self.fields))})"

            recordParams = []
            for field in self.fields:
                if field not in record:
                    continue
                mod = self.tableFieldInfo[field]["mods"]
                if mod == "None":
                    item = record[field]
                elif mod == "integer":
                    item = int(record[field])
                elif mod == "dict":
                    item = json.dumps(record[field])

                recordParams.append(item)

            cursor.execute(query, tuple(recordParams))
            connection.commit()
        finally:
            connection.close()

    def getAnyRecord(self):
        connection = sqlite3.connect(self.fileName)
        cursor = connection.cursor()
        try:
            query = f"""
                    SELECT *
                    FROM {self.tableName}
                    ORDER BY priority DESC, id ASC
                    LIMIT 1
                """
            cursor.execute(query)

            record = cursor.fetchone()

            if not record:
                return None

            returnDict = {}
            
            for ind, field in enumerate(self.fields):
                mod = self.tableFieldInfo[field]["mods"]

                if mod == "None":
                    item = record[ind]
                elif mod == "integer":
                    item = str(record[ind])
                elif mod == "dict":
                    item = json.loads(record[ind])

                returnDict[field] = item

            return returnDict
        finally:
            connection.close()

    def getRecordByVal(self, params, vals):
        connection = sqlite3.connect(self.fileName)
        cursor = connection.cursor()
        try:
            whereParams = []
            for param, val in zip(params, vals):
                whereParams.append(f"{param}={val}")

            query = f"""
                    SELECT *
                    FROM {self.tableName}
                    WHERE {" AND ".join(whereParams)}
                    ORDER BY id ASC
                    LIMIT 1
                """

            cursor.execute(query)

            record = cursor.fetchone()

            if not record:
                return None

            returnDict = {}
            
            for ind, field in enumerate(self.fields):
                mod = self.tableFieldInfo[field]["mods"]

                if mod == "None":
                    item = record[ind]
                elif mod == "integer":
                    item = str(record[ind])
                elif mod == "dict":
                    item = json.loads(record[ind])

                returnDict[field] = item

            return returnDict
        finally:
            connection.close()

    def deleteRecord(self, recordID):
        connection = sqlite3.connect(self.fileName)
        cursor = connection.cursor()
        try:
            cursor.execute(
                f"DELETE FROM {self.tableName} WHERE id = ?",
                (recordID,)
            )

            connection.commit()
        finally:
            connection.close()

    def clearDB(self):
        connection = sqlite3.connect(self.fileName)
        cursor = connection.cursor()
        try:
            cursor.execute(f"DELETE FROM {self.tableName}")
        finally:
            connection.close()