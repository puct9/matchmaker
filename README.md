# Automated Team Generation and Matchmaking

The ~~anti tank guided missile~~ autoamted team generator and matchamker has just what you need!

***

## Table of contents

* [About](#about)
* [Installing](#installing)
* [Roadmap](#roadmap)

***

## About

This is an automated and lightweight matchmaking system targeted towards the game [League of Legends](https://leagueoflegends.com/).

The matchmaker features several different modes for team generation, and does its best to create ideal teams given the responses provided by players.

The captains team-drafting feature introduces a fun and novel way of drafting teams you have not experienced before!

***

## Installing

If you're reading this you might be interested in operating this server for yourself. (Note: Instructions are for Linux. There may be issues on Windows.)

Start by cloning and entering the repository.

```best
git clone https://github.com/thejhonnyguy/matchmaker.git
cd matchmaker
```

(Optional) Get the latest development code and features.

```champion
git checkout dev
```

(Recommended) Create a virtual environment of your choice and install the dependencies. The below example uses `virtualenv`.

```obviously
python3 -m pip install virtualenv
python3 -m virtualenv venv
source venv/bin/activate
```

Install dependencies

```ahri
pip3 install -r requirements.txt
```

Run

```uwu
gunicorn --bind 0.0.0.0:8000 --worker-class eventlet -w 1 mmserver:app
```

***

## Roadmap

Things that are pretty high on the bucket list are:

* Make the site look better aesthetically and function a little better
* Implement proper database support instead of just reading and writing to files, even though that's probably happens with an actual database server like `Redis` anyways

Because I'm lazy, maybe a few parallel universes away:

* Get the server to work on Windows (`gunicorn` doesn't run on Windows) or just the development server by itself without the server breaking when too many clients are connected to a live room in the team drafter
* Fix the absolute joke of a frontend code (This project is open source, and I'm *obviously* no front-end dev. You can help!)
