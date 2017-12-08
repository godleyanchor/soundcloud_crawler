import pickle
import random
import networkx as nx
from itertools import count
from collections import Counter
import matplotlib.pyplot as plt

class SoundCloudNetwork():
    def __init__(self):
        self.artists = {}
        self.network = nx.DiGraph()
        self.attr_names = ['num_tracks', 'num_followers', 'artist_city', 'latitude', 'longitude']
        # 0=num_tracks, 1=num_followers, 2=artist_city, 3=latitude, 4=longitude
        self.attrs = [{}, {}, {}, {}, {}]
        self.correct_attrs = [{}, {}, {}, {}, {}]
        self.artist_id_dict = {}

    def gen_network(self, edge_list="soundcloud_edge_list.txt", attr="soundcloud_attr.txt", read_attr=True):
        self.network = nx.read_edgelist(edge_list)
        if read_attr:
            self.read_attr(attr_fname=attr)

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

    def link_prediction(self, graph_on):
        iterations = 20
        # Define arrays for axes
        probs = np.linspace(0,1,num=200).tolist()
        sc_accs = []

        # Use a for loop to compute the accuracy of GbA heuristic for different probabilites
        for prob in probs:
            sh_acc = 0
            # Use another loop to average the fraction of correct guesses
            for i in range(iterations):
                # Reload the graphs to delete all of the node attributes
                gen_network(read_attr=False)

                # Open the attribute files and set the node attributes for each of the graphs
                attr_range = read_attr(percentage_observed=prob)

                # Predict what the remaining unlabeled nodes should have for a label
                sh_acc += predict_labels(attr_range=attr_range)

            print(round(prob*200))
            sc_accs.append(sh_acc / iterations)

        # Store data to save on computation time
        with open("soundcloud_link_pred_accs.p", "wb") as f:
            pickle.dump(sc_accs, f)

        if graph_on:
            # Plot the graphs with the collected data
            plt.scatter(probs, nor_accs, label='Accuracy')
            plt.xlabel("Percent of Nodes Observed")
            plt.ylabel("GbA Heuristic Accuracy")
            plt.title('GbA Heuristic Accuracy vs Percent of Nodes Observed for the SoundCloud Network')
            plt.legend(loc='lower right')
            plt.show()

    # Function used to predict the nonexistent labels in the graph based on the given labels
    def predict_labels(self, attr_range):
        acc = 0
        total_unlabeled_nodes = 0
        current_attr = nx.get_node_attributes(self.network, self.attrs[-1])

        # Cycle through each of the nodes in the graph
        for node in self.network.nodes():
            # If no label exists
            if not node in current_attr:
                neighbor_attr = []
                # Cycle through each of the neighbors and store their attributes
                for neighbor in nx.all_neighbors(self.network, node):
                    if neighbor in current_attr:
                        neighbor_attr.append(current_attr[neighbor])
                # If any of the neighbors did have an attribute, find the most frequent attribute
                if len(neighbor_attr) != 0:
                    data = Counter(neighbor_attr)
                    random.shuffle(neighbor_attr)
                    most_frequent = max(neighbor_attr, key=data.get)
                    current_attr[node] = most_frequent
                # Otherwise assign a random attribute
                else:
                    most_frequent = random.randint(attr_range[0],attr_range[-1])
                current_attr[node] = most_frequent
                # Compute the accuracy of the assigned label
                if len(self.attrs) != 1:
                    if current_attr[node] == self.correct_attrs[-1][node]:
                        acc += 1
                else:
                    if current_attr[node] == self.correct_attrs[node]:
                        acc += 1

                total_unlabeled_nodes += 1

        if total_unlabeled_nodes == 0:
            acc = 1
        else:
            acc = acc/total_unlabeled_nodes
        return acc

    def read_attr(self, percentage_observed=1, attr_fname="soundcloud_attr.txt"):
        # Create a random sample of nodes to observe the attributes for the GbA heuristic
        nodes_observed = random.sample(self.network.nodes(), int(len(self.network.nodes()) * percentage_observed))

        # Open the file and append the attributes to a dict
        with open(attr_fname, 'r') as attr_file:
            for line in attr_file:
                line_splitted = line.split('\t')
                id_split = line_splitted[0]
                # Populate the attribute of the node if it's apart of the sample
                if id_split in nodes_observed:
                    for i, attr in enumerate(line_splitted):
                        if i:
                            self.attrs[i-1][id_split] = attr
                # For each of the attributes
                # num_tracks, num_followers, artist_city, latitude, longitude
                for i, attr in enumerate(line_splitted):
                    if i:
                        self.correct_attrs[i-1][id_split] = attr

        # Set the node attributes on the graph
        for attr_name, attr in zip(self.attr_names, self.attrs):
            nx.set_node_attributes(self.network, attr_name, attr)

        # Find the unique range of classes
        cn = Counter(self.correct_attr[-1].values())
        attr_range = sorted(k for k in cn.keys())

        return attr_range

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
    #sc.gen_edge_list()
    #sc.gen_attr()
    sc.gen_network()
    #sc.print_network()
    sc.triangle_scores()
    sc.clustering_coef()
if __name__ == '__main__':
    main()
