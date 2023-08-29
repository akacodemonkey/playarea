import os
import requests
import logging
import re

def __get_headers():
  return {
    "Content-Type": "application/json",
    "accept": "application/json"
}

def __get_url(path, base_url=__get_value("JIRA_URI")):
  return base_url + path

def __get_value(env_var):
  if env_var in os.environ:
    return os.environ.get(env_var)

  raise ValueError(f"Environment variable {env_var} not set")

def __get_label(fields, key):
  def get_key(value):
    return value.split('=')[0]
  
  def get_value(value):
    return value.split('=')[1]

  results = [ get_value(label) for label in fields["labels"] if get_key(label) == key]
  return results[0] if len(results) > 0 else ""

def __get_match(expression, text):
  match = re.search(expression, text)

  if match:
    return match[0]

  return ""

def __matches(expression, text):
  if re.search(expression, text) == None:
    return False
  else:
    return True

def __update_issue(issue):
  id = issue["id"]
  key = issue["key"]

  print(f"processing ticket {key}")
  url = __get_label(issue["fields"], "url")
  labels_to_add = []

  account = __get_match(r"aws-.*?\.", url)

  labels_to_add.append({"add": "enc=aws"})
  labels_to_add.append({"add": f"account={account}"})

  
  if len(labels_to_add) > 0:
    data = {
      "update": {
        "labels": labels_to_add
      }
    }

    print(f"updating record {key} with {data}")
    response = requests.put(__get_url(f"issue/{id}"),
                      auth=(__get_value("JIRA_USER"), __get_value("JIRA_PWD")),
                      headers=__get_headers(),
                      json=data)

    response.raise_for_status()



def update_tickets():
  logging.info("pulling down all open jira tickets")

  start_at=0
  number_results=100
  loop = True

  while loop:
    search = {
                "startAt": start_at,
                "maxResults": number_results,
                "fields": ["labels", "created"],
                "jql": __get_value("QUERY")
              }

    response = requests.post(__get_url("search"),
                          auth=(__get_value("JIRA_USER"), __get_value("JIRA_PWD")),
                          headers=__get_headers(),
                          json=search)

    response.raise_for_status()
    json_data = response.json()

    [__update_issue(issue) for issue in json_data["issues"]]

    if len(json_data["issues"]) == 0:
      loop = False
    
    start_at = start_at + number_results
