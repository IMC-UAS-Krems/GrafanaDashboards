import json

from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
    loader=FileSystemLoader(searchpath="templates"),
    autoescape=select_autoescape("json"),
)
env.filters["jsonify"] = json.dumps

pie = env.get_template("pie_chart.json")
scatter = env.get_template("scatter.json")
config = env.get_template("config.json")

pie = json.loads(pie.render(parts=["one", "two", "three"], title="Pie Chart"))
scatter = json.loads(scatter.render(x="one", y=["two", "three"], title="Scatter Chart"))
config = json.loads(config.render(config={"plots": [pie, scatter]}))

print(json.dumps(config, indent=4))
