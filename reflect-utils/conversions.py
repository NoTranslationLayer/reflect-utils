# initialize an empty map of reflection name to dataframe
# load Reflections JSON with list of reflection instances
# iterate through list of reflection instances
# if the reflection name is new, create a dataframe for that reflection and add it to the map
# for each reflection instance, iterate through list of metrics
# each reflection instance corresponds to a row in that reflection's dataframe
# the metric "kind" field determines how the value is parsed from JSON
# each metric corresponds to a column in the reflection dataframe
# to get the name of the column, use the "kind", <kind>, "_0", "name" value
# if the metric "recorded" is false, leave the cell empty
# if the metric kind is "choice", parse "kind", "_0", "choice", "value" 
# if the metric kind is "bool", parse "bool", "_0", "bool"
# if the metric kind is "unit", parse "unit", "_0", "value" 
# if the metric kind is "rating", parse "rating", "_0", "score" 
# if the metric kind is "string", parse "string", "_0", "string"

import pandas as pd
import json

def parse_metrics(metrics):
    df_row = {}
    for metric in metrics:
        if metric['recorded']:
            kind = list(metric['kind'].keys())[0]
            column_name = metric['kind'][kind]['_0']['name']
            if kind == 'choice':
                df_row[column_name] = metric['kind'][kind]['_0']['choice']
            elif kind == 'bool':
                df_row[column_name] = metric['kind'][kind]['_0']['bool']
            elif kind == 'unit':
                df_row[column_name] = metric['kind'][kind]['_0']['value']
            elif kind == 'rating':
                df_row[column_name] = metric['kind'][kind]['_0']['score']
            elif kind == 'string':
                df_row[column_name] = metric['kind'][kind]['_0']['string']
    return df_row

def parse_reflection(reflection):
    name = reflection['name']
    date = reflection['date']
    metrics = parse_metrics(reflection['metrics'])
    metrics['date'] = date
    metrics['id'] = reflection['id']
    metrics['notes'] = reflection['notes']
    return name, pd.DataFrame([metrics])

def parse_json(json_string):
    data = json.loads(json_string)
    reflections_map = {}
    for reflection in data:
        name, df = parse_reflection(reflection)
        if name in reflections_map:
            reflections_map[name] = pd.concat([reflections_map[name], df])
        else:
            reflections_map[name] = df
    return reflections_map
