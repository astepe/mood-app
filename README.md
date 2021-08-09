# mood-app

Track your mood daily.

## Description

Register a new user onto the mood-app, login everyday and record your mood to maintain a streak, track how your mood has changed over time and see how your longest streak compares with other users' longest streaks.

## Getting Started

### Dependencies

* Docker

### Installing

* Clone this repository onto your local system using `git clone https://github.com/astepe/mood-app.git`

### Starting Containers

1. Move into the top-level directory
```
cd mood-app/
```

2. Run Docker Compose
```
docker compose up --build
```

### Usage
#### Registering a New User
request:
```
curl --location --request POST 'http://0.0.0.0:5000/user' \
--header 'Content-Type: application/json' \
--data-raw '{
    "username": "joeSchmo",
    "password": "1234"
}'
```
response:
```
{
    "username": "joeSchmo"
}
```
#### Getting all User's Moods
request:
```
curl -u joeSchmo:1234 --location --request GET 'http://0.0.0.0:5000/mood'
```
response:
```
{
    "currentStreak": 0,
    "longestStreak": 0,
    "moodHistory": [
        {
            "date": "Sun, Oct 24 at 06:28 PM",
            "mood": "CHEERFUL"
        }
    ]
}
```
#### Logging a User's Mood
request:
```
curl -u joeSchmo:1234 --location --request POST 'http://0.0.0.0:5000/mood' \
--header 'Content-Type: application/json' \
--data-raw '{
    "mood": "WHIMSICAL",
    "timestamp": 1635200114
}'
```
response:
```
{
    "currentStreak": 1,
    "longestStreak": 1,
    "moodHistory": [
        {
            "date": "Mon, Oct 25 at 10:15 PM",
            "mood": "WHIMSICAL"
        },
        {
            "date": "Sun, Oct 24 at 06:28 PM",
            "mood": "CHEERFUL"
        }
    ],
    "streakPercentile": 66.67
}
```
### Read/Write Trade-offs
Deriving the user's current streak percentile each time they interact with the `/mood` resource is potentially a very expensive task (O(n*logn + n) in the worst case) because the system needs to evaluate how the user's current longest streak compares with all other user's longest streaks during the time of the request. Furthermore, each time a user's longest streak increases, any or all other users' percentiles could be affected by the change. Their percentiles would need to be adjusted accordingly.

#### Cached Calculations
Rather than perform these adjustments for each read, they should instead be made each time a user's longest streak changes. Each user will have his/her pre-computed percentile stored in the database for quick lookups. This dramatically improves read performance while increasing the time it takes to perform writes (only when a longest streak changes).

#### Streak Percentile Consistency
In order to ensure that all streak percentiles remain consistent during concurrent longest streak updates, all user rows must be locked (`SELECT ... FOR UPDATE`) by any transaction that is making percentile adjustments. This could potentially have a detrimental effect on availability if many requests are attempting to update streak percentiles at once. One way to lessen the impact of this locking would be to move streak percentile data into its own table.

## On Scaling Up
To scale the application to higher numbers of users, the following design changes could be explored to improve availability, scalability and security.
### Horizontal Scaling/Replication
In order to support higher request throughput, improve availability, and allow for more flexible deployment strategies (e.g. blue-green or canary) the application and/or the database can be replicated across multiple servers. Application auto-scaling could be implemented through 3rd party container-orchestration tools like Kubernetes or AWS ECS. Database scaling and replication could be managed by tools such as AWS RDS Aurora.
### Reverse-Proxy/Load Balancer
Adding a layer 7 load balancer such as Nginx or AWS ALB will provide 2 key benefits:
1. We will have more control over how traffic is ditributed to our application servers. We can adjust the strategy (e.g. round-robin, weighted etc.) based on business needs or performance requirements.
2. The load balancer will act as a buffer in front of our application servers to mitigate certain security risks such as denial-of-service attacks and provide centralized SSL encryption.
### Token-Based Authentication
Rather than requiring the user to send their username and password for each request they make to the API, a jwt token with a set expiration time can be provided to the user after they log into the application. This token can then be sent by the user for each request. This limits the risk that the user's credentials could be exposed. 
### Query Optimization
One benefit of using an ORM like sqlalchemy is that it abstracts away the underlying SQL commands from the user which helps to speed up the development process. The drawback here is that we now have less visibility into the efficiency of the SQL statements being issued by the ORM. Open tracing tools like Jaeger could be instrumented to get a view into what underlying SQL statements are being issued to the database in order to quickly identify ways to optimize SQL queries.
### Gunicorn Gevent Workers
In order for our Flask application to serve thousands of concurrent requests at one time with minimal memory overhead, we can configure Gunicorn to use multiple gevent workers. Since our application is mostly I/O bound (especially when re-calculating streak percentiles due to loading all user rows from the database), non-blocking I/O calls to the database will free up workers to serve more requests while the application waits for the database to respond.
