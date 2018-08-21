#!/bin/sh
set -e
# Start StanfordCoreNLP server
cd bin/stanford-corenlp-full-2015-12-09
java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 &
cd ../..
##
python3 src/main.py load_corpus --goldstd cemp_sample
python3 src/main.py train --goldstd cemp_sample --models models/cemp_classifier
python3 src/main.py test --goldstd cemp_sample -o pickle data/cemp_self_test --models models/cemp_classifier
python3 src/evaluate.py evaluate cemp_sample --results data/cemp_self_test --models models/cemp_classifier
