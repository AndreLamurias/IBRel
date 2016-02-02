# coding=utf-8
import os
import logging
import time
import sys
from operator import itemgetter
import pprint
from nltk.stem.porter import *
import re
from collections import Counter
import operator

from text.corpus import Corpus
from text.document import Document
import xml.etree.ElementTree as ET
from classification.re.relations import Pairs


class TempEvalCorpus(Corpus):
    """
    TempEval corpus used for NER and RE on the SemEval - Clinical tempeval 2015.
    self.path is the base directory of the files of this corpus.
    """
    
    def __init__(self, corpusdir, **kwargs):
        super(TempEvalCorpus, self).__init__(corpusdir, **kwargs)
        self.invalid_sections = (20104, 20105, 20116, 20138)

    def load_corpus(self, corenlpserver):        
        # self.path is the base directory of the files of this corpus
        
#         if more than one file:
        trainfiles = [self.path + f for f in os.listdir(self.path) if not f.endswith('~')] # opens all files in folder (see config file)
        for openfile in trainfiles:
            print("file: "+openfile)
            with open(openfile, 'r') as inputfile:
                newdoc = Document(inputfile.read(), process=False, did=os.path.basename(openfile), title = "titulo_"+os.path.basename(openfile)) 
            newdoc.process_document(corenlpserver, "biomedical") #process_document chama o tokenizer
            valid = True
            invalid_sids = []
            for s in newdoc.sentences:
                if s.text in ['[start section id="{}"]'.format(section) for section in self.invalid_sections]:
                    valid = False
                if not valid:
                    invalid_sids.append(s.sid)
                if s.text in ['[end section id="{}"]'.format(section) for section in self.invalid_sections]:
                    valid = True
                if (s.text.startswith("[") and s.text.endswith("]")) or s.text.istitle():
                    newdoc.title_sids.append(s.sid)
            newdoc.invalid_sids = invalid_sids
            logging.debug("invalid sentences: {}".format(invalid_sids))
            logging.debug("title sentences: {}".format(newdoc.title_sids))
            self.documents[newdoc.did] = newdoc
    
    def get_invalid_sentences(self):
        for did in self.documents:
            self.documents[did].invalid_sids = []
            valid = True
            invalid_sids = []
            for s in self.documents[did].sentences:
                if s.text in ['[start section id="{}"]'.format(section) for section in self.invalid_sections]:
                    valid = False
                if not valid or s.text.startswith("[meta"):
                    invalid_sids.append(s.sid)
                if s.text in ['[end section id="{}"]'.format(section) for section in self.invalid_sections]:
                    valid = True
            self.documents[did].invalid_sids = invalid_sids
            logging.debug("invalid sentences: {}".format(invalid_sids))

    def load_annotations(self, ann_dir):
        self.stemmer = PorterStemmer()
        self.get_invalid_sentences()
        logging.info("Cleaning previous annotations...")
        for did in self.documents:
            for s in self.documents[did].sentences:
                if "goldstandard" in s.entities.elist:
                    s.entities.elist["goldstandard"] = []
        traindirs = os.listdir(ann_dir) # list of directories corresponding to each document
        trainfiles = []
        for d in traindirs:
            fname = ann_dir + "/" + d + "/" + d + ".Temporal-Relation.gold.completed.xml"
            fname2 = ann_dir + "/" + d + "/" + d + ".Temporal-Entity.gold.completed.xml"
            if os.path.isfile(fname):
                trainfiles.append(fname)
            elif os.path.isfile(fname2):
                    trainfiles.append(fname2)
            else:
                print "no annotations for this doc: {}".format(d)

        total = len(trainfiles)
        logging.info("loading annotations...")
        stats = {}
        relation_words = {}
        for current, f in enumerate(trainfiles):
            logging.debug('%s:%s/%s', f, current + 1, total)
            with open(f, 'r') as xml:
                #parse DDI corpus file
                t = time.time()
                root = ET.fromstring(xml.read())
                did = traindirs[current]
                if did not in self.documents:
                    print "no text for this document: {}".format(did)
                    # sys.exit()
                    continue
                annotations = root.find("annotations")
                self.load_entities(annotations, did)
                all_words = Counter(re.split("\W", self.documents[did].text.lower()))

                doc_stats, doc_words = self.load_relations(annotations, did, all_words)
                for k in doc_stats:
                    if k not in stats:
                        stats[k] = 0
                    stats[k] += doc_stats[k]
                for t in doc_words:
                    if t not in relation_words:
                        relation_words[t] = {}
                    for w in doc_words[t]:
                        if w not in relation_words[t]:
                            relation_words[t][w] = 0
                        relation_words[t][w] += doc_words[t][w]
        pp = pprint.PrettyPrinter()
        pp.pprint(stats)
        for t in relation_words:
            relation_words[t] = sorted(relation_words[t].items(), key=operator.itemgetter(1))[-20:]
            relation_words[t].reverse()
        pp.pprint(relation_words)


    def load_entities(self, annotations_tag, did):
        entity_list = []
        for entity in annotations_tag.findall("entity"):
            span = entity.find("span").text
            if ";" in span:
                # entity is not sequential: skip for now
                continue
            span = span.split(",")
            start = int(span[0])
            end = int(span[1])
            entity_type = entity.find("type").text
            entity_id = entity.find("id").text
            entity_list.append((start, end, entity_type, entity_id))
        entity_list = sorted(entity_list, key=itemgetter(0)) # sort by start
        for e in entity_list:
            # print e, self.documents[did].text[e[0]:e[1]]
            entity_text = self.documents[did].text[e[0]:e[1]]
            if e[2] in ("EVENT", "TIMEX3", "SECTIONTIME", "DOCTIME"): # choose type: TIMEX3 or EVENT (also SECTIONTIME and DOCTIME)
                # print e, self.documents[did].text[e[0]:e[1]]
                sentence = self.documents[did].find_sentence_containing(e[0], e[1], chemdner=False)
                if sentence is not None:
                    # e[0] and e[1] are relative to the document, so subtract sentence offset
                    start = e[0] - sentence.offset
                    end = e[1] - sentence.offset
                    sentence.tag_entity(start, end, e[2].lower(), text=entity_text, original_id=e[3])
                else:
                    print "could not find sentence for this span: {}-{}".format(e[0], e[1])


    def load_relations(self, annotations_tag, did, allwords):
        stats = {"path_count": 0, "clinic_count": 0,
                 "path_doc_chars": 0, "clinic_doc_chars": 0,
                 "path_nentities": 0, "clinic_nentities": 0,
                 "path_nrelations": 0, "clinic_nrelations": 0,
                 "path_relation_dist": 0, "clinic_relation_dist": 0,
                 "path_event_time": 0, "path_time_event": 0, "path_time_time": 0, "path_event_event": 0,
                 "clinic_event_time": 0, "clinic_time_event": 0, "clinic_time_time": 0, "clinic_event_event": 0,

                 "path_nevent_source": 0, "path_ntime_source": 0,
                 "clinic_nevent_source": 0, "clinic_ntime_source": 0,
                 "path_nevent_target": 0, "path_ntime_target": 0,
                 "clinic_nevent_target": 0, "clinic_ntime_target": 0,
                 "clinic_multisentence":0, "path_multisentence": 0}

        wordsdic = {"path_event_time": {}, "path_time_event": {}, "path_time_time": {}, "path_event_event": {},
                 "clinic_event_time": {}, "clinic_time_event": {}, "clinic_time_time": {}, "clinic_event_event": {}}
        if "path" in did:
            doc_type = "path_"
        else:
            doc_type = "clinic_"
        stats[doc_type + "count"] += 1
        stats[doc_type + "doc_chars"] += len(self.documents[did].text)
        source_relation = {} # (source original id, target original id, relation original id)
        entity_list = {} # all entities of this document original_id => entity
        for relation in annotations_tag.findall("relation"):
            stats[doc_type + "nrelations"] += 1
            props = relation.find("properties")
            source_id = props.find("Source").text
            target_id = props.find("Target").text
            relation_type = relation.find("type").text
            relation_id = relation.find("id").text
            if source_id not in source_relation:
                source_relation[source_id] = []
            source_relation[source_id].append(target_id)
        self.documents[did].pairs = Pairs()
        for sentence in self.documents[did].sentences:
            if "goldstandard" in sentence.entities.elist:
                for entity in sentence.entities.elist["goldstandard"]:
                    entity_list[entity.original_id] = entity
                    stats[doc_type + "nentities"] += 1
        for eid in entity_list:
            entity = entity_list[eid]
            entity.targets = []
            if entity.original_id in source_relation:
                for target in source_relation[entity.original_id]:
                    if target not in entity_list:
                        print "target not in entity list:", target
                    else:
                        pairwordsdic = {}
                        entity.targets.append(entity_list[target].eid)
                        e2 = get_entity(self.documents[did], entity_list[target].eid)
                        # print "{}:{}=>{}:{}".format(entity.type, entity.text, e2.type, e2.text)
                        # print "||{}||".format(self.documents[did].text[entity.dstart:e2.dend])

                        stats[doc_type + "relation_dist"] += len(self.documents[did].text[entity.dend:e2.dstart])
                        stats[doc_type + "n{}_source".format(entity.type)] += 1
                        stats[doc_type + "n{}_target".format(e2.type)] += 1
                        stats[doc_type + "{}_{}".format(entity.type, e2.type)] += 1

                        words = re.split("\W", self.documents[did].text[entity.dend:e2.dstart].lower())
                        #stems = set()
                        stems = []
                        for w in words:
                            if w.strip() == "":
                                continue
                            #if w.isdigit():
                            #    stem = "#digit#"
                            #else:
                                #stem = self.stemmer.stem(w)
                            #    stem = w
                            #stems.add(stem)
                            stems.append(w)
                        for stem in stems:
                            if stem not in pairwordsdic:
                                pairwordsdic[stem] = 0
                            pairwordsdic[stem] += 1


                        if e2.sid != entity.sid:
                            stats[doc_type + "multisentence"] += 1
                        for stem in pairwordsdic:
                            if stem not in wordsdic[doc_type + "{}_{}".format(entity.type, e2.type)]:
                                wordsdic[doc_type + "{}_{}".format(entity.type, e2.type)][stem] = 0
                            wordsdic[doc_type + "{}_{}".format(entity.type, e2.type)][stem] += pairwordsdic[stem]*1.0/allwords[stem]
                """        # logging.debug("multi-sentence:{}+{}".format(sentence1.text, sentence2.text))
                        chardist = e2.dstart - e1.dend
                        if chardist > maxdist[0] and e1.type != "time" and not e1.text.isupper():
                            print e1.type
                            maxdist = (chardist, "{}=>{}".format(e1, e2))
                        # logging.debug("dist between entities: {}".format(chardist))"""
                    # logging.debug("|{}|=>|{}|".format(e1.text, e2.text))
                    #self.documents[did].add_relation(e1, e2, "tlink", relation=True)
                """    npairs += 1
                elif '\n' not in self.documents[did].text[e1.dstart:e2.dend] or e1.text.isupper() or e1.type == "time":
                    self.documents[did].add_relation(e1, e2, "tlink", relation=False)
                    npairs += 1
                if (e2.original_id, e1.original_id) in relation_list:
                    inverted += 1"""
                """    if e1.sid != e2.sid:
                        sentence1 = self.documents[did].get_sentence(e1.sid)
                        sentence2 = self.documents[did].get_sentence(e2.sid)
                        # logging.debug("multi-sentence:{}+{}".format(sentence1.text, sentence2.text))
                        chardist = e2.dstart - e1.dend
                        if chardist > maxdist[0] and e2.type != "timex3" and not e2.text.isupper():
                            #print e2.type
                            maxdist = (chardist, "{}<={}".format(e1, e2))
                        # logging.debug("dist between entities: {}".format(chardist))

                    # logging.debug("|{}|<=|{}|".format(e1.text, e2.text))
                    self.documents[did].add_relation(e2, e1, "tlink", relation=True, original_id=relation_id)
                else:
                    self.documents[did].add_relation(e2, e1, "tlink", relation=False, original_id=relation_id)"""
        return stats, wordsdic


def get_entity(document, eid, source="goldstandard"):
	for sentence in document.sentences:
		if source in sentence.entities.elist:
			for e in sentence.entities.elist[source]:
				if e.eid == eid:
					return e
	print "no entity found for eid {}".format(eid)
	return None

