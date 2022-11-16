import math
from enum import Enum
import networkx as nx

from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa.space import NetworkGrid


class State(Enum):
    VULNERABLE = 0
    HARDENED = 1
    INFLUENCED = 2
    RESILIENT = 3


def number_state(model, state):
    return sum(1 for a in model.grid.get_all_cell_contents() if a.state is state)

def number_influenced(model):
    return number_state(model, State.INFLUENCED)

def number_hardened(model):
    return number_state(model, State.HARDENED)

def number_vulnerable(model):
    return number_state(model, State.VULNERABLE)

def number_resilient(model):
    return number_state(model, State.RESILIENT)


class SocialInfluenceModel(Model):
    """A social influence model with some number of agents"""

    def __init__(
        self,
        number_influencers=1,
        influence_chance=0.4,
        influence_check_frequency=0.4,
        reintegration_probability=0.3,
        resilience_chance=0.3,
        gain_hardened_chance=0.5,
    ):

        
        ### epinions network ###
        epinions = nx.read_weighted_edgelist('/Users/clarkpetri/Documents/GMU/CSS 600/Class Project/epinions_small.csv', delimiter=',')

        # Get largest connected component
        n = max(nx.connected_components(epinions), key=len)
        connected_g = nx.subgraph(epinions, n)
        numEdges = connected_g.number_of_edges()
        numNodes = connected_g.number_of_nodes()

        # Get list of highest degree nodes
        node_degree_list = sorted(connected_g.degree, key=lambda x: x[1], reverse=True)
        temp = node_degree_list[0:10]
        top_ten = []
        for n in temp:
            top_ten.append(n[0])

        prob = 1

        self.G = connected_g # test_net

        self.grid = NetworkGrid(self.G)
        self.schedule = RandomActivation(self)
        self.number_influencers = (number_influencers if number_influencers <= len(top_ten) else len(top_ten))
        self.influence_chance = influence_chance
        self.influence_check_frequency = influence_check_frequency
        self.reintegration_probability = reintegration_probability
        self.resilience_chance = resilience_chance
        self.gain_hardened_chance = gain_hardened_chance

        self.datacollector = DataCollector(
            {
                "Influenced": number_influenced,
                "Vulnerable": number_vulnerable,
                "Resilient": number_resilient,
                "Hardened": number_hardened,
            }
        )

        # Create agents
        for i, node in enumerate(self.G.nodes()):
            a = InfluenceAgent(
                i,
                self,
                State.VULNERABLE,
                self.influence_chance,
                self.influence_check_frequency,
                self.reintegration_probability,
                self.resilience_chance,
                self.gain_hardened_chance,
            )
            self.schedule.add(a)
            # Add the agent to the node
            self.grid.place_agent(a, node)


        ### PLACE INFLUENCER ###
        ### AT PRESENT, THIS IS RANDOM ###
        ### We can explicitly place it later ###
        influencer_start = self.random.sample(top_ten, self.number_influencers)
        for a in self.grid.get_cell_list_contents(influencer_start):
            a.state = State.INFLUENCED

        self.running = True
        self.datacollector.collect(self)

    def resilient_vulnerable_ratio(self):
        try:
            return number_state(self, State.RESILIENT) / number_state(
                self, State.VULNERABLE
            )
        except ZeroDivisionError:
            return math.inf

    def step(self):
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)

    def run_model(self, n):
        for i in range(n):
            self.step()


class InfluenceAgent(Agent):
    def __init__(
        self,
        unique_id,
        model,
        initial_state,
        influence_chance,
        influence_check_frequency,
        reintegration_probability,
        resilience_chance,
        gain_hardened_chance,
    ):
        super().__init__(unique_id, model)

        self.state = initial_state

        self.influence_chance = influence_chance
        self.influence_check_frequency = influence_check_frequency
        self.reintegration_probability = reintegration_probability
        self.resilience_chance = resilience_chance
        self.gain_hardened_chance = gain_hardened_chance
        

    def try_to_influence(self):
        neighbors_nodes = self.model.grid.get_neighbors(self.pos, include_center=False)
        vulnerable_neighbors = [
            agent
            for agent in self.model.grid.get_cell_list_contents(neighbors_nodes)
            if agent.state is State.VULNERABLE
        ]
        for a in vulnerable_neighbors:
            if self.random.random() < self.influence_chance:
                a.state = State.INFLUENCED

    def gain_resilience(self):
        if self.random.random() < self.resilience_chance:
            self.state = State.RESILIENT

    def try_remove_influence(self):
        # Try to remove
        if self.random.random() < self.reintegration_probability:
            # Success

            if self.random.random() < self.resilience_chance:
                self.state = State.RESILIENT

            else:
                self.state = State.VULNERABLE
                
        else:
            # Failed
            self.state = State.INFLUENCED

    ### This is where the magic for hardened will happen I think...
    def try_check_situation(self):

        # Agent has been influenced and based on random against check frequency, we see how they change
        # Really, this is a probabilistic slider for how frequently we want the influenced to have a 
        # chance to change state
        if self.random.random() < self.influence_check_frequency:
            
            if self.state is State.INFLUENCED:

                # Are they permanently influenced?
                if self.random.random() < self.gain_hardened_chance:
                    self.state = State.HARDENED
                # If not, go through influence removal booleans which in turn calls chance 
                # of resiliency gain
                else:
                    self.try_remove_influence()

    def step(self):
        #if self.state == State.RESILIENT:
            #print("I'M RESILIENT")
        #if self.state == State.HARDENED:
            #print("I'M HARDENED")
        if self.state is State.INFLUENCED:
            self.try_to_influence()
        if self.state is State.HARDENED:
            self.try_to_influence()
        self.try_check_situation()