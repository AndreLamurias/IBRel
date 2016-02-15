import codecs
import time
import logging
import sys
import os
import xml.etree.ElementTree as ET
from xml.etree import ElementTree as ET

import progressbar as pb
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '../..'))
from text.corpus import Corpus
from text.document import Document
from text.sentence import Sentence

type_match = {"Specific_miRNAs": "mirna",
              "Non-Specific_miRNAs": "mirna",
              "Genes/Proteins": "protein"}
class MirnaCorpus(Corpus):
    def __init__(self, corpusdir, **kwargs):
        super(MirnaCorpus, self).__init__(corpusdir, **kwargs)
        self.subtypes = ["miRNA", "disease", "protein"]

    def load_corpus(self, corenlpserver, process=True):
        # self.path is just one file with every document
        time_per_abs = []
        with open(self.path, 'r') as xml:
            t = time.time()
            root = ET.fromstring(xml.read())
            all_docs = root.findall("document")
            widgets = [pb.Percentage(), ' ', pb.Bar(), ' ', pb.AdaptiveETA(), ' ', pb.Timer()]
            pbar = pb.ProgressBar(widgets=widgets, maxval=len(all_docs)).start()
            for i, doc in enumerate(all_docs):
                doctext = ""
                did = doc.get('id')
                doc_sentences = [] # get the sentences of this document
                doc_offset = 0 # offset of the current sentence relative to the document
                for sentence in doc.findall('sentence'):
                    sid = sentence.get('id')
                    #logging.info(sid)
                    text = sentence.get('text')
                    #text = text.replace('\r\n', '  ')
                    doctext += " " + text # generate the full text of this document
                    this_sentence = Sentence(text, offset=doc_offset, sid=sid, did=did)
                    doc_offset = len(doctext)
                    doc_sentences.append(this_sentence)
                newdoc = Document(doctext, process=False, did=did)
                newdoc.sentences = doc_sentences[:]
                newdoc.process_document(corenlpserver, "biomedical")
                self.documents[newdoc.did] = newdoc
                abs_time = time.time() - t
                time_per_abs.append(abs_time)
                pbar.update(i+1)
            pbar.finish()
        abs_avg = sum(time_per_abs)*1.0/len(time_per_abs)
        logging.info("average time per abstract: %ss" % abs_avg)

    def getOffsets(self, offset):
        # check if its just one offset per entity or not
        # add 1 to offset end to agree with python's indexes
        offsets = []
        offsetList = offset.split(';')
        for o in offsetList:
            offsets.append(int(o.split('-')[0]))
            offsets.append(int(o.split('-')[1])+1)

        #if len(offsets) > 2:
        #    print "too many offsets!"
            #sys.exit()
        return offsets

    def load_annotations(self, ann_dir, etype):
        time_per_abs = []
        logging.info("loading miRNA annotations...")
        with open(ann_dir, 'r') as xml:
            #parse DDI corpus file
            t = time.time()
            root = ET.fromstring(xml.read())
            for doc in root.findall("document"):
                did = doc.get('id')
                for sentence in doc.findall('sentence'):
                    sid = sentence.get('id')
                    this_sentence = self.documents[did].get_sentence(sid)
                    if this_sentence is None:
                        print did, sid, "sentence not found!"
                        for entity in sentence.findall('entity'):
                            print entity.get('charOffset'), entity.get("type")
                        print [s.sid for s in self.documents[did].sentences]
                        sys.exit()
                        #continue
                    for entity in sentence.findall('entity'):
                        eid = entity.get('id')
                        entity_offset = entity.get('charOffset')
                        offsets = self.getOffsets(entity_offset)
                        entity_type = type_match.get(entity.get("type"))
                        #print this_sentence.text[offsets[0]:offsets[-1]], entity.get("text")
                        #if "protein" in entity_type.lower() or "mirna" in entity_type.lower():
                        if entity_type and (etype == "all" or (etype != "all" and etype == entity_type)):
                            this_sentence.tag_entity(offsets[0], offsets[-1], entity_type,
                                                     text=entity.get("text"))


def get_ddi_mirna_gold_ann_set(goldpath, entitytype):
    logging.info("loading gold standard... {}".format(goldpath))
    gold_offsets = set()
    with open(goldpath, 'r') as xml:
        #parse DDI corpus file
        t = time.time()
        root = ET.fromstring(xml.read())
        for doc in root.findall("document"):
            did = doc.get('id')
            doctext = ""
            for sentence in doc.findall('sentence'):
                sentence_text = sentence.get('text')
                #sentence_text = sentence_text.replace('\r\n', '  ')
                for entity in sentence.findall('entity'):
                    entity_offset = entity.get('charOffset')
                    if ";" in entity_offset:
                        continue
                    offsets = entity_offset.split("-")
                    start, end = int(offsets[0]) + len(doctext), int(offsets[1]) + len(doctext) + 1
                    etype = type_match.get(entity.get("type"))
                    #print this_sentence.text[offsets[0]:offsets[-1]], entity.get("text")
                    #if "protein" in entity_type.lower() or "mirna" in entity_type.lower():
                    if etype == entitytype:
                        gold_offsets.add((did, start, end, entity.get("text")))

                doctext += " " + sentence_text # generate the full text of this document
    logging.debug(gold_offsets)
    logging.debug(len(gold_offsets))
    return gold_offsets