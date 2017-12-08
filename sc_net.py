#!/usr/bin/env python3

import pickle
import networkx as nx
import matplotlib.pyplot as plt
import random
from itertools import count

class SoundCloudNetwork():
    def __init__(self):
        self.artists = {}
        self.network = nx.DiGraph()
        self.attr_names = ['num_tracks', 'num_followers', 'artist_city', 'latitude', 'longitude']
        # 0=num_tracks, 1=num_followers, 2=artist_city, 3=latitude, 4=longitude
        self.attrs = [{}, {}, {}, {}, {}]
        self.artist_id_dict = {}

    def gen_network(self, edge_list="soundcloud_edge_list.txt", attr="soundcloud_attr.txt"):
        self.network = nx.read_edgelist(edge_list)
        self.read_attr(attr)

    def triangle_scores(self):
        triangles = nx.triangles(self.network)
        num_triangles = 0
        for value in triangles.values():
            num_triangles += value
        print("num_triangles: %s\t" % num_triangles)
        print("triangles: %s\t" % triangles)

    def clustering_coef(self):
        clustering_coefs = nx.clustering(self.network)
        print("clustering_coefs: %s\t" % clustering_coefs)

    def link_prediction(self):
        pass

    def infect(self, p):
                
        # Set all nodes to "Susceptible" 
        nx.set_node_attributes(self.network, 'epidemia', "S")

        # Select node at random to begin infection
        seed = random.randint(0, self.network.number_of_nodes()-1)
        self.network.node[seed]['epidemia'] = "I"
        infected = []
        infected.append(seed)

        # For every node that gets infected
        t = 0
        total_infected = 1
        while(1):

            new_infected_list = []
            new_infected_count = 0
            for i in infected:

                # Try all neighbors
                for edge in self.network.neighbors(i):

                    # If edge is susceptible
                    if self.network.node[edge]['epidemia'] == "S":

                        # Try and infect it
                        if random.random() < p:
                            self.network.node[edge]['epidemia'] = "I"
                            new_infected_list.append(edge)
                            new_infected_count += 1
                            total_infected += 1

            print("New Infections: %s", new_infected_list)
            infected = new_infected_list
            t += 1

            if new_infected_count <= 0:
                break

        print("p = %s\t| t = %d\t| total infected = %d" % (p, t, total_infected) )
        
        return t, total_infected
        
    def frange(self, start, stop, step):
        i = start
        while i < stop:
            yield i
        i += step

    def SI(self):
        p_list = []
        t_list = []
        infected_list = []
        for p in self.frange(0, 1, 0.1):
            t, num_infected = self.infect(p)
            
            p_list.append(p)
            t_list.append(t)
            infected_list.append(float(num_infected) / self.network.number_of_nodes())

        plt.title("Infected Length vs Probability of Infection")
        plt.plot(p_list, t_list)
        plt.xlabel("Probability of Infection")
        plt.ylabel("Length of Infection (time steps)")
        plt.savefig("soundcould_infection_length.png")
        plt.clear()

        plt.title("Infected Percentage vs Probability of Infection")
        plt.plot(p_list, infected_list)
        plt.xlabel("Probability of Infection")
        plt.ylabel("Percent Infected")
        plt.savefig("soundcould_infection_percent.png")
        plt.clear()

        #plt.show()

    def read_attr(self, attr_fname):
        # Open the file and append the attributes to a dict
        with open(attr_fname, 'r') as attr_file:
            for line in attr_file:
                line_splitted = line.split('\t')
                id_split = line_splitted[0]
                # For each of the attributes
                # num_tracks, num_followers, artist_city, latitude, longitude
                for i, attr in enumerate(line_splitted):
                    if i:
                        self.attrs[i-1][id_split] = attr

        # Set the node attributes on the graph
        for attr_name, attr in zip(self.attr_names, self.attrs):
            nx.set_node_attributes(self.network, attr_name, attr)

    def print_network(self):
        # Create a color array for plotting
        node_groups = set(nx.get_node_attributes(self.network,'num_tracks').values())
        mapping = dict(zip(sorted(node_groups),count()))
        nodes = self.network.nodes()
        colors = [[mapping[self.network.node[node]['num_tracks']] for node in nodes]]

        # Draw the soundcloud network
        nx.draw_networkx(self.network, with_labels=True, labels=self.attrs[0], node_color=colors, font_size=12, node_size=10, cmap='cool')
        plt.show()

    def load_artists(self, fname="artists.p"):
        self.artists = pickle.load(open(fname, "rb"))
        for artist in self.artists.keys():
            self.artist_id_dict[artist] = self.artists[artist]['id']
            self.artist_id_dict[self.artists[artist]['id']] = artist
        print(self.artist_id_dict)

    def dump_artists(self, fname="artists.p"):
        pickle.dump(self.artists, open(fname, "wb"))


    def gen_edge_list(self, filename="soundcloud_edge_list.txt"):
        f = open(filename,'w')
        for artist in self.artists.keys():
            print(artist)
            try:
                followers = self.artists[artist]["followers"]
            except:
                followers = []
            for follower in followers:
                #print('\t', follower)
                f.write((str(self.artists[artist]['id']) + ' ' + str(self.artists[follower]['id']) + '\n'))
                print("artist_id: %s\t follower_id: %s" % (self.artists[artist]['id'], self.artists[follower]['id']))
        f.close()

    def gen_attr(self, filename="soundcloud_attr.txt"):
        f = open(filename,'w')
        for artist in self.artists.keys():
            num_tracks = self.try_key(artist, 'num_tracks')
            num_followers = self.try_key(artist, 'num_followers')
            artist_city = self.try_key(artist, 'city')
            latitude = self.try_key(artist, 'latitude')
            longitude = self.try_key(artist, 'longitude')
            f.write((str(self.artists[artist]['id']) + '\t ' + str(self.artists[artist]['num_tracks']) + '\t ' + str(self.artists[artist]['num_followers']) + '\t ' + self.artists[artist]['city'] + '\t ' + str(self.artists[artist]['latitude']) + '\t ' + str(self.artists[artist]['longitude']) + '\n'))
            print("name: %s\t num_tracks: %s\t num_followers: %s\t artist_city: %s" % (artist, self.artists[artist]['num_tracks'], self.artists[artist]['num_followers'], self.artists[artist]['city']))
            #print("artist_id: %s\t artist_name: %s" % (self.artists[artist]['id'], artist))
        f.close()

    def try_key(self, artist, key):
        try:
            var = self.artists[artist][key]
            return var
        except:
            self.artists[artist][key] = ''
            return ''

def main():
    sc = SoundCloudNetwork()
    sc.load_artists("artist_small.p")
    sc.gen_edge_list()
    sc.gen_attr()
    sc.gen_network()
    print("artists: %s" % (sc.network.number_of_nodes()))
    #sc.print_network()
    #sc.triangle_scores()
    #sc.clustering_coef()
    sc.SI()
if __name__ == '__main__':
    main()
