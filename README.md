# Server for Home Server:

## The Reason:
Before I went to college, I started a project that would allow me to help manage my productivity, a home server.
By having a home server, I could offload computing tasks, have my own cloud storage (using NextCloud) and other 
potential applications.

- **Listener**:
  Listens on the WebSocket connection for incoming jobs.
- **Job Queue Manager**:
  Adds and removes jobs from the job queue.
  Redundancy measures in place through JSON file to ensure security in case of abrupt outages.
- **Job Selector**:
  Selects job based on priority from job queue passing it on to the router.
- **Router**:
  Based on the endpoint of the job submitted, it's routed to the appropriate tool, keeping a track of the status
  of each tool and availability
- **Tools**:
  Different tools with different functionalities, each with it's own endpoint.
- **Result Queue Manager**:
  Adds and removes results from the result queue.
  Similar redundancy measures to the job queue.
- **Result Selector**:
  Selects results from the result queue.
- **Sender**:
  Sends results over the WebSocket connection.

**Potential improvements in functionality**:
If the whole system is to be made asynchronous, then each tool could directly call the `Sender`.
