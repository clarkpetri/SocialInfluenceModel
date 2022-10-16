import math

#browser visualization features for mesa
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import ChartModule
from mesa.visualization.modules import NetworkModule
from mesa.visualization.modules import TextElement
from .model import SocialInfluenceModel, State, number_influenced


def network_portrayal(G): 
    # The model ensures there is always 1 agent per node

    def node_color(agent):
        return {State.INFLUENCED: "#FF0000", State.VULNERABLE: "#008000",
        State.HARDENED: "#808080", State.RESILIENT: "0000FF"}.get(agent.state, "#808080")

    def edge_color(agent1, agent2):
        if State.RESILIENT in (agent1.state, agent2.state):
            return "#000000"
        return "#e8e8e8"

    def edge_width(agent1, agent2):
        if State.RESILIENT in (agent1.state, agent2.state):
            return 3
        return 2

    def get_agents(source, target):
        return G.nodes[source]["agent"][0], G.nodes[target]["agent"][0]

    portrayal = dict()
    portrayal["nodes"] = [
        {
            "size": 6,
            "color": node_color(agents[0]),
            "tooltip": f"id: {agents[0].unique_id}<br>state: {agents[0].state.name}",
        }
        for (_, agents) in G.nodes.data("agent")
    ]

    ### TEST CODE FROM GITHUB ###

    nodes = []
    node_label_to_node_id = {}
    node_id = 0
    for node_label, agents in G.nodes.data("agent"):
        agent = agents[0]
        nodes.append({
            "size": 6,
            "color": node_color(agent),
            "tooltip": f"id: {agent.unique_id}<br>state: {agent.state.name}",
        })
        node_label_to_node_id[node_label] = node_id
        node_id += 1

    portrayal = dict()
    portrayal["nodes"] = nodes

    portrayal["edges"] = [
        {
            "source": node_label_to_node_id[source],
            "target": node_label_to_node_id[target],
            "color": edge_color(*get_agents(source, target)),
            "width": edge_width(*get_agents(source, target)),
        }
        for (source, target) in G.edges
    ]

    ### END TEST ###

    # portrayal["edges"] = [
    #     {
    #         "source": source,
    #         "target": target,
    #         "color": edge_color(*get_agents(source, target)),
    #         "width": edge_width(*get_agents(source, target)),
    #     }
    #     for (source, target) in G.edges
    # ]

    return portrayal


network = NetworkModule(network_portrayal, 500, 500)#, library="d3")
chart = ChartModule(
    [
        {"Label": "Influenced", "Color": "#FF0000"},
        {"Label": "Vulnerable", "Color": "#008000"},
        {"Label": "Resilient", "Color": "0000FF"},
        {"Label": "Hardened", "Color": "#808080"},
    ]
)


class MyTextElement(TextElement):
    def render(self, model):
        ratio = model.resilient_vulnerable_ratio()
        ratio_text = "&infin;" if ratio is math.inf else f"{ratio:.2f}"
        influenced_text = str(number_influenced(model))

        return "Resilient/Vulnerable Ratio: {}<br>Influenced Remaining: {}".format(
            ratio_text, influenced_text
        )


model_params = {
    "influence_chance": UserSettableParameter(
        "slider",
        "Influence Chance",
        0.4,
        0.0,
        1.0,
        0.1,
        description="Probability that vulnerable neighbor will be influenced",
    ),
    "influence_check_frequency": UserSettableParameter(
        "slider",
        "Influence Check Frequency",
        0.4,
        0.0,
        1.0,
        0.1,
        description="Frequency the nodes check whether they are influenced by " "a influencer",
    ),
    "reintegration_probability": UserSettableParameter(
        "slider",
        "Reintegration Probability",
        0.3,
        0.0,
        1.0,
        0.1,
        description="Probability an individual will lose their influenced status",
    ),
    "resilience_chance": UserSettableParameter(
        "slider",
        "Gain Resilience Chance",
        0.3,
        0.0,
        1.0,
        0.1,
        description="Probability that a recovered agent will become "
        "resilient to influence in the future",
    ),
    "gain_hardened_chance": UserSettableParameter(
        "slider",
        "Gain Hardened Chance",
        0.5,
        0.0,
        1.0,
        0.1,
        description="Probability that an agent will harden and remain permanently influenced",
    ),
}

### Assuming we can add monitors in the server.py file, is this where we would add histograms or line graphs
### for the network measurements, or would that need to be added to the model.py file? 

server = ModularServer(
    SocialInfluenceModel, [network, MyTextElement(), chart], "Social Influence Model", model_params
)
server.port = 8521
