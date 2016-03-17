from __future__ import unicode_literals
import logging
import sys
import itertools
import re
from classification.rext.kernelmodels import ReModel
from classification.results import ResultsRE
from config import config


class RuleClassifier(ReModel):
    def __init__(self, corpus, ptype, rules=["same_line", "list_items", "dist", "same_text", "all"]):
        """
        Rule based classifier
        rules: List of rules to use
        """
        self.rules = rules
        self.ptype = ptype
        self.corpus = corpus
        self.pairs = {}
        self.pids = {}
        self.trigger_words = set([])


    def load_classifier(self):
        pass

    def test(self):
        pcount = 0
        ptrue = 0
        for did in self.corpus.documents:
            doc_entities = self.corpus.documents[did].get_entities("goldstandard")
            # logging.debug("sentence {} has {} entities ({})".format(sentence.sid, len(sentence_entities), len(sentence.entities.elist["goldstandard"])))
            # doc_entities += sentence_entities
            for pair in itertools.permutations(doc_entities, 2):
                sid1 = pair[0].eid.split(".")[-2]
                sid2 = pair[1].eid.split(".")[-2]
                sn1 = int(sid1[1:])
                sn2 = int(sid2[1:])
                if abs(sn2 - sn1) > 0:
                    continue
                pid = did + ".p" + str(pcount)
                self.pids[pid] = pair
                self.pairs[pid] = 0
                # sentence1 = self.corpus.documents[did].get_sentence(e1.sid)
                # sentence2 = self.corpus.documents[did].get_sentence(e2.sid)
                # logging.info("relation: {}=>{}".format(pair[0].type, pair[1].type))
                if pair[0].type in config.pair_types[self.ptype]["source_types"] and\
                   pair[1].type in config.pair_types[self.ptype]["target_types"]:
                    # logging.info("mirna-dna relation: {}=>{}".format(pair[0].text, pair[1].text))
                    self.pairs[pid] = 1
                    ptrue += 1
                elif pair[1].type in config.pair_types[self.ptype]["source_types"] and\
                     pair[0].type in config.pair_types[self.ptype]["target_types"]:
                    self.pids[pid] = (pair[1], pair[0])
                    self.pairs[pid] = 1
                    ptrue += 1
                pcount += 1



    def get_predictions(self, corpus):
        results = ResultsRE("")
        # print len(self.pids)
        for p, pid in enumerate(self.pids):
            if self.pairs[pid] < 1:
                # pair.recognized_by["rules"] = -1
                pass
            else:
                did = ".".join(pid.split(".")[:-1])
                pair = corpus.documents[did].add_relation(self.pids[pid][0], self.pids[pid][1], self.ptype, relation=True)
                #pair = self.get_pair(pid, corpus)
                results.pairs[pid] = pair
                pair.recognized_by["rules"] = 1
                logging.info("{0.eid}:{0.text} => {1.eid}:{1.text}".format(pair.entities[0],pair.entities[1]))
            #logging.info("{} - {} SST: {}".format(pair.entities[0], pair.entities[0], score))
        results.corpus = corpus
        return results



