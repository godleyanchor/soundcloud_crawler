import pickle
import networkx as nx
from itertools import count
import matplotlib.pyplot as plt

class SoundCloudNetwork():
    def __init__(self):
        self.artists = {}
        self.network = nx.DiGraph()
        self.attr_names = ['num_tracks', 'num_followers', 'artist_city', 'latitude', 'longitude']
        # 0=num_tracks, 1=num_followers, 2=artist_city, 3=latitude, 4=longitude
        self.attrs = [{}, {}, {}, {}, {}]

    def gen_network(self, edge_list="soundcloud_edge_list.txt", attr="soundcloud_attr.txt"):
        self.network = nx.read_edgelist(edge_list)
        self.read_attr(attr)

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
    sc.print_network()
if __name__ == '__main__':
    main()
