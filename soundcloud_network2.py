import sys
import pickle
import random
import operator
import numpy as np
import pandas as pd
import networkx as nx
from itertools import count
from sklearn import metrics
from collections import Counter
import matplotlib.pyplot as plt

class SoundCloudNetwork():
    def __init__(self):
        self.artists = {}
        self.network = nx.Graph()
        self.attr_names = ['num_tracks', 'num_followers', 'artist_city', 'latitude', 'longitude']
        # 0=num_tracks, 1=num_followers, 2=artist_city, 3=latitude, 4=longitude
        self.attrs = [{}, {}, {}, {}, {}]
        self.correct_attrs = [{}, {}, {}, {}, {}]
        self.artist_id_dict = {}

    # Generate a network based on an edgelist and load attributes or not based on read_attr var passed
    def gen_network(self, edge_list="soundcloud_edge_list.txt", attr="soundcloud_attr.txt", read_attr=True):
        self.network = nx.read_edgelist(edge_list)
        if read_attr:
            self.read_attr(attr_fname=attr)

    # Analysis function for the number of triangles in the current network
    def triangle_scores(self):
        triangles = nx.triangles(self.network)
        num_triangles = 0
        for value in triangles.values():
            num_triangles += value
        print("num_triangles: %s\t" % num_triangles)
        #print("triangles: %s\t" % triangles)

    # Analysis function for the degrees of nodes in the current network
    def degree_scores(self):
        degrees = self.network.degree()
        max_degree_key = max(degrees.items(), key=operator.itemgetter(1))[0]
        print("max_degree_key: %s\t" % max_degree_key)
        print("max_degree_value: %s\t" % degrees[max_degree_key])
        print("max_degree_artist: %s" % self.artist_id_dict[int(max_degree_key)])
        degree_sum = 0
        for degree in degrees.values():
            degree_sum += degree
        degree_avg = degree_sum / len(degrees.keys())
        print("degree_avg: %s" % degree_avg)
        df = pd.DataFrame([degrees])
        df = df.T
        df.hist()
        plt.show()

    # Analysis function for the clustering coefficient on nodes
    def clustering_coef(self):
        clustering_coefs = nx.clustering(self.network)
        max_coef_key = max(clustering_coefs.items(), key=operator.itemgetter(1))[0]
        print("max_coef_key: %s\t" % max_coef_key)
        print("max_coef_value: %s\t" % clustering_coefs[max_coef_key])
        print("max_coef_artist: %s" % self.artist_id_dict[int(max_coef_key)])
        coef_sum = 0
        for coef in clustering_coefs.values():
            coef_sum += coef
        coef_avg = coef_sum / len(clustering_coefs.keys())
        print("coef_avg: %s" % coef_avg)
        df = pd.DataFrame([clustering_coefs])
        df = df.T
        df.hist()
        plt.show()

    # Function used to implement link prediction
    def link_prediction(self, load_file=True, graph_on=True):
        # Define arrays for axes
        num_probs = 10
        probs = np.linspace(0,1,num=num_probs).tolist()
        if load_file:
            # Store data to save on computation time
            with open("soundcloud_gba_heuristic_accs.p", "rb") as f:
                sc_accs = pickle.load(f)
            with open("soundcloud_link_pred_accs.p", "rb") as f:
                lr_accs = pickle.load(f)
        else:
            iterations = 2
            sc_accs = []
            lr_acc = [0, 0, 0]
            lr_accs = [[] for i in range(3)]
            temp = [[] for i in range(3)]

            # Use a for loop to compute the accuracy of GbA heuristic for different probabilites
            for prob in probs:
                sh_acc = 0
                #print("prob: ", prob)
                # Use another loop to average the fraction of correct guesses
                for i in range(iterations):
                    # Reload the graph to delete all of the node attributes
                    self.gen_network(read_attr=False)

                    # Open the attribute files and set the node attributes for each of the graphs
                    attr_range = self.read_attr(percentage_observed=prob)
                    #print(len(self.attrs[0]))

                    # Predict what the remaining unlabeled nodes should have for a label
                    sh_acc += self.predict_labels(attr_range=attr_range)

                    # # Create a new empty graph for link link_prediction
                    # self.network = nx.Graph()
                    #
                    # # Read in the percentage of edges based on frac into each Network
                    # self.read_edges(prob)
                    #
                    # # Predict what the remaining edges should be based on the three heuristics
                    # temp[0], temp[1], temp[2] = self.predict_edges()
                    # for j in range(len(lr_acc)):
                    #     lr_acc[j] += temp[j]

                print(round(prob*num_probs))
                sc_accs.append(sh_acc / iterations)
                # for i in range(len(lr_accs)):
                #     lr_accs[i].append(lr_acc[i]/iterations)
                #     lr_acc[i] = 0

        # Store data to save on computation time
        with open("soundcloud_gba_heuristic_accs.p", "wb") as f:
            pickle.dump(sc_accs, f)
        with open("soundcloud_link_pred_accs.p", "wb") as f:
            pickle.dump(lr_accs, f)

        if graph_on:
            # Plot the graphs with the collected data
            plt.scatter(probs, sc_accs, label='Accuracy')
            plt.xlabel("Percent of Nodes Observed")
            plt.ylabel("GbA Heuristic Accuracy")
            plt.title('GbA Heuristic Accuracy vs Percent of Nodes Observed for the SoundCloud Network')
            plt.legend(loc='lower right')
            plt.show()

            plt.plot(probs, lr_accs[0], label='Degree Product AUC', color='g', linestyle='-')
            plt.plot(probs, lr_accs[1], label='Common Neighbors AUC', color='b', linestyle='--')
            plt.plot(probs, lr_accs[2], label='Shortest Path AUC', color='r', linestyle='-.')
            plt.xlabel("Percent of Edges Observed")
            plt.ylabel("AUC for Different Heuristics")
            plt.title('Different Heuristic Accuracies vs Percent of Edges Observed for the SoundCloud Network')
            plt.legend(loc='lower right')
            plt.show()

    # Function used to predict the nonexistent edges in the graph based on three different heuristics
    def predict_edges(self, edge_list="soundcloud_edge_list.txt"):
        original_network = nx.read_edgelist(edge_list)
        scores = [[] for i in range(3)]
        ys = [[] for i in range(3)]
        degree_product_score = {}
        common_neighbor_score = {}
        geodesic_path_score = {}
        if len(self.network.degree().values()) != 0:
            max_degree = max(self.network.degree().values())
            min_degree = min(self.network.degree().values())
        else:
            max_degree = 0
            min_degree = 0

        # Cycle through each of the nodes in the graph
        for x, i in enumerate(self.network.nodes()):
            # Calculate the degree of the current node i
            i_degree = self.network.degree(i)
            # Find the set of neighbors for i
            i_neighbors = self.network.neighbors(i)
            # Cycle through all of the possible connections each node could have
            for j in self.network.nodes():
                # Cannot connect to itself
                if i != j:
                    # If an edge doesn't exist
                    if not (i, j) in self.network.edges():
                        # Calculate the degree of the current node j
                        j_degree = self.network.degree(j)
                        # Find the set of neighbors for j
                        j_neighbors = self.network.neighbors(j)

                        # Find the degree product score
                        if max_degree and max_degree-min_degree:
                            degree_product_score[i, j] = (i_degree * j_degree - min_degree) / (max_degree * max_degree - min_degree)
                        else:
                            degree_product_score[i, j] = 0
                        scores[0].append(degree_product_score[i, j])

                        # Find the normalized common neighbor score
                        if (len(list(set(i_neighbors) | set(j_neighbors)))):
                            common_neighbor_score[i, j] = (len(list(set(i_neighbors) & set(j_neighbors)))) / (len(list(set(i_neighbors) | set(j_neighbors))))
                            scores[1].append(common_neighbor_score[i, j])
                        else:
                            scores[1].append(random.random()/len(self.network.nodes()))

                        # Find the shortest path between nodes i and j and compute the socre
                        try:
                            geodesic_path_score[i, j] = 1 / (len(nx.shortest_path(self.network, i, j)) - 1)
                            scores[2].append(geodesic_path_score[i, j])
                        except nx.NetworkXNoPath:
                            scores[2].append(random.random()/len(self.network.nodes()))

                        # Compute the true y's for the AUC function
                        if original_network.has_edge(i, j):
                            ys[0].append(1)
                            ys[1].append(1)
                            ys[2].append(1)
                            # print("Degree score: ", scores[0][-1])
                            # print("Common Neighbors score: ", scores[1][-1])
                            # print("Shortest path score: ", scores[2][-1])
                        else:
                            ys[0].append(0)
                            ys[1].append(0)
                            ys[2].append(0)

        # Calculate the AUC for each of the heuristics
        fpr = [[] for i in range(3)]
        tpr = [[] for i in range(3)]
        accs = [[] for i in range(3)]
        for i in range(3):
            if len(scores[i]) != 0 and len(ys[i]) != 0:
                zipped = zip(scores[i], ys[i])
                sorted_zipped = sorted(zipped)
                new_scores = [score[0] for score in sorted_zipped]
                new_ys = [y[1] for y in sorted_zipped]
                fpr[i], tpr[i], thresholds = metrics.roc_curve(new_ys, new_scores, pos_label=1)
                accs[i] = metrics.auc(fpr[i], tpr[i])
            else:
                accs[i] = 0

        print("Accs: ", accs)
        return accs[0], accs[1], accs[2]

    # Function used to read in the fraction of edges for the link prediction function
    def read_edges(self, fraction_observed, edge_list="soundcloud_edge_list.txt"):
        original_graph = nx.read_edgelist(edge_list)
        edges_observed = random.sample(original_graph.edges(), int(len(original_graph.edges()) * fraction_observed))
        self.network.add_edges_from(edges_observed)

    # Function used to predict the nonexistent labels in the graph based on the given labels
    def predict_labels(self, attr_range):
        acc = 0
        total_unlabeled_nodes = 0
        current_attr = nx.get_node_attributes(self.network, self.attr_names[0])
        #print('len of current attrs: ', len(self.attrs[0].keys()))
        #print('len of correct attrs: ', len(self.correct_attrs[0].keys()))
        #print(len(current_attr.keys()))

        # Cycle through each of the nodes in the graph
        for node in self.network.nodes():
            # If no label exists
            if not node in current_attr.keys():
                neighbor_attr = []
                # Cycle through each of the neighbors and store their attributes
                for neighbor in nx.all_neighbors(self.network, node):
                    if neighbor in current_attr.keys():
                        # print(current_attr[neighbor])
                        neighbor_attr.append(current_attr[neighbor])
                # print("neighbors: ")
                # for i in nx.all_neighbors(self.network, node):
                #      print(i)
                # Compute the accuracy of the assigned label
                acc += self.compute_accuracy1(neighbor_attr, current_attr, node, attr_range)

                total_unlabeled_nodes += 1

        if total_unlabeled_nodes == 0:
            acc = 1
        else:
            acc = acc/total_unlabeled_nodes
        return acc

    # One accuracy function for link prediction
    def compute_accuracy(self, neighbor_attr, current_attr, node, attr_range):
        # If any of the neighbors did have an attribute, find the most frequent attribute
        if len(neighbor_attr) != 0:
            data = Counter(neighbor_attr)
            random.shuffle(neighbor_attr)
            most_frequent = max(neighbor_attr, key=data.get)
            current_attr[node] = most_frequent
        # Otherwise assign a random attribute
        else:
            most_frequent = random.choice(attr_range)
        current_attr[node] = most_frequent
        # print("most frequent: ", most_frequent)

        # Compute the accuracy of the assigned label
        if len(self.attrs) != 1:
            if current_attr[node] == self.correct_attrs[0][node]:
                # print("node: ", node)
                # print("current_attr: ", current_attr[node])
                # print("current_attr: ", self.correct_attrs[0][node])
                return 1
            else:
                return 0
        else:
            if current_attr[node] == self.correct_attrs[node]:
                return 1
            else:
                return 0

    # One accuracy function for link prediction
    def compute_accuracy1(self, neighbor_attr, current_attr, node, attr_range):
        # If any of the neighbors did have an attribute, find the most frequent attribute
        if len(neighbor_attr) != 0:
            zero_count = 0
            non_zero_count = 0
            print(neighbor_attr)
            for attr in neighbor_attr:
                if attr == '0':
                    zero_count += 1
                else:
                    non_zero_count += 1
            if zero_count >= non_zero_count:
                most_frequent = 0
            else:
                most_frequent = 1
        # Otherwise assign a random attribute
        else:
            most_frequent = random.choice([0,1])
        current_attr[node] = most_frequent
        print("most frequent: ", most_frequent)

        # Compute the accuracy of the assigned label
        if len(self.attrs) != 1:
            if (not current_attr[node] and not self.correct_attrs[0][node]) or (current_attr[node] and self.correct_attrs[0][node]):
                return 1
            else:
                return 0
        else:
            if (not current_attr[node] and not self.correct_attrs[node]) or (current_attr[node] and self.correct_attrs[node]):
                return 1
            else:
                return 0

    # Function used to read in the attr file and load the attributes onto nodes in the network (pass a percentage for link prediction)
    def read_attr(self, percentage_observed=1, attr_fname="soundcloud_attr.txt"):
        # Create a random sample of nodes to observe the attributes for the GbA heuristic
        nodes_observed = random.sample(self.network.nodes(), int(len(self.network.nodes()) * percentage_observed))

        # Open the file and append the attributes to a dict
        with open(attr_fname, 'r', encoding="utf-8") as attr_file:
            for line in attr_file:
                line = line.replace(" ", "")
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
        cn = Counter(self.correct_attrs[0].values())
        attr_range = sorted(k for k in cn.keys() if k != ' ')

        return attr_range

    # Print the structure of the network (Use only on networks with nodes<500)
    def print_network(self):
        # Create a color array for plotting
        node_groups = set(nx.get_node_attributes(self.network,'num_tracks').values())
        mapping = dict(zip(sorted(node_groups),count()))
        nodes = self.network.nodes()
        colors = [[mapping[self.network.node[node]['num_tracks']] for node in nodes]]

        # Print the number of nodes and edges in the networks
        print('Num nodes: %s' % len(nodes))
        print('Num edges: %s' % self.network.number_of_edges())

        # Draw the soundcloud network
        nx.draw_networkx(self.network, with_labels=True, labels=self.attrs[0], node_color=colors, font_size=12, node_size=10, cmap='cool')
        plt.show()

    # Load the self.artists dict into memory from a file defined by fname
    def load_artists(self, fname="artists.p"):
        self.artists = pickle.load(open(fname, "rb"))
        i = 0
        for artist in self.artists.keys():
            self.artists[artist]['id'] = i
            i += 1
            self.artist_id_dict[artist] = self.artists[artist]['id']
            self.artist_id_dict[self.artists[artist]['id']] = artist

    # Dump the current self.artists dict
    def dump_artists(self, fname="artists.p"):
        pickle.dump(self.artists, open(fname, "wb"))

    # Generates the edgelist file to be loaded into a network based on self.artists
    def gen_edge_list(self, filename="soundcloud_edge_list.txt"):
        f = open(filename,'w')
        keys = ["followers", "following"]
        for artist in self.artists.keys():
            #print("artist: ", artist)
            for key in keys:
                try:
                    followers = self.artists[artist][key]
                except:
                    followers = []
                for follower in followers:
                    #print('\t', follower)
                    # For when the data is cleaned for link prediction
                    if follower in self.artists.keys():
                        f.write((str(self.artists[artist]['id']) + ' ' + str(self.artists[follower]['id']) + '\n'))
                    #print("artist_id: %s\t follower_id: %s" % (self.artists[artist]['id'], self.artists[follower]['id']))

        f.close()

    # Generates the attribute file to be loaded into a network based on self.artists
    def gen_attr(self, filename="soundcloud_attr.txt"):
        f = open(filename,'w', encoding="utf-8")
        for artist in self.artists.keys():
            num_tracks = self.try_key(artist, 'num_tracks')
            num_followers = self.try_key(artist, 'num_followers')
            artist_city = self.try_key(artist, 'city')
            latitude = self.try_key(artist, 'latitude')
            longitude = self.try_key(artist, 'longitude')
            f.write((str(self.artists[artist]['id']) + '\t ' + str(self.artists[artist]['num_tracks']) + '\t ' + str(self.artists[artist]['num_followers']) + '\t ' + str(self.artists[artist]['city']) + '\t ' + str(self.artists[artist]['latitude']) + '\t ' + str(self.artists[artist]['longitude']) + '\n'))
            #print("name: %s\t num_tracks: %s\t num_followers: %s\t artist_city: %s" % (artist, self.artists[artist]['num_tracks'], self.artists[artist]['num_followers'], self.artists[artist]['city']))
        f.close()

    # Helper function to key into self.artists[artist] metadata, creates an empty field if none exists
    def try_key(self, artist, key):
        try:
            var = self.artists[artist][key]
            return var
        except:
            if key == "num_tracks" or key == "num_followers" or key == "num_following":
                self.artists[artist][key] = 0
                return 0
            else:
                self.artists[artist][key] = ''
                return ''

    # Function used to delete any artist without any metadata
    def clean_artist_lr(self):
        new_artists = {}
        i = 0
        for artist in self.artists:
            if not self.try_key(artist, 'num_tracks') == 0:
                new_artists[artist] = self.artists[artist]
                new_artists[artist]['id'] = i
                i += 1
        self.artists = new_artists
        i = 0
        self.artist_id_dict = {}
        for artist in self.artists.keys():
            self.artists[artist]['id'] = i
            i += 1
            self.artist_id_dict[artist] = self.artists[artist]['id']
            self.artist_id_dict[self.artists[artist]['id']] = artist
        print(len(self.artists.keys()))

def main():
    sc = SoundCloudNetwork()
    sc.load_artists("pickled_files/artists_large_connected.p")
    #sc.load_artists("artists_genres.p")
    #sc.clean_artist_lr()
    sc.gen_edge_list(filename="soundcloud_edge_list2.txt")
    sc.gen_attr(filename="soundcloud_attr2.txt")
    #sc.gen_network()
    #sc.print_network()
    #sc.triangle_scores()
    #sc.clustering_coef()
    #sc.degree_scores()
    #sc.SI()
    sc.link_prediction(False, True)
    #sc.print_network()
if __name__ == '__main__':
    main()
