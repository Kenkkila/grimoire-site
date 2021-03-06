# Grimoire Site

## What
This site, www.grimoire.org, exposes a neo4j graph database of metadata about historical grimoires.
The goal is to look at the connections between different texts, find overlapping content,
and provide a reference point for information about the books and their contents.

## How
To get an instance running:
- Fork this repo and clone it to your development environment
```bash
$ git clone https://github.com/[your_username]/grimoire-site.git
```

- Create a virtual environment and install dependencies
```bash
$ virtualenv .
$ source bin/activate
$ pip install -r requirements.txt
```

- [Install Neo4j](http://neo4j.com/download/) version 2.3.8
- Open Neo4j and select the `grimoire-site/database/` directory as your database
- Set the environment variables `NEO4J_USER` and `NEO4J_PASS` to the Neo4j user and password
- Run the application
```bash
$ python runserver.py
```
