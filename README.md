## GitHub repo events aggregation

- ❌ The application can monitor up to five configurable repositories
- ❌ It generates statistics based on a rolling window of either 7 days or 500 events whichever is less
- ✅ These statistics are made available to end-users via a REST API
- ✅ the API will show the average time between consecutive events, separately for each combination of event type and repository name
- ✅ The application should minimize requests to the GitHub API
- ✅ retain data through application restarts

## How to run it
- start a virtual environment
- activate it
- install requirements.txt
- run `python main.py`
- the app is served on host="127.0.0.1", port=8000
- for documentation go to the served app and add /docs

## What is missing
### configurable repositories
The idea was that another endpoint would be exposed to the API user in which they could specify
up to 5 repositories in the body of the request. This would be then written either in the database or
in python config file.

The main statistics serving endpoint then would not require repo/owner specifications and by default would
return all the configured combinations. In case of user sending some specific combination to the main
endpoint without this combo being configured, then it would throw a response asking the user the reconfigure.

### statistics on rolling window
The data_magic function would have to be expanded to address this desired feature

### reasonable documentation
With FastAPI having one of its forte out-of-the-box swagger documentation I think I have underused it.
Pydantic feature of defining request/response were not used and so the API documentation is not as flashy
as I imagined it would be.

### other remarks
It might've saved me a lot of time to turn the response into a class. There was a lot of repetitive object passing
which for me signals that a class should've been used. Repo and owner were passsed almost everywhere. That's a cool
upgrade opportunity.

I really wanted to work on my type hinting, but I didn't make it a priority and then I was out of time.

In `data_manipulation.py` there is a lot of repeated code.