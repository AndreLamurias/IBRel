#!/bin/sh
set -x
LOGLEVEL=${1:-WARNING}

# Load train corpora
#python src/main.py load_corpus --goldstd jnlpba_train --log $LOGLEVEL --entitytype protein
#python src/main.py load_corpus --goldstd bc2gm_train --log $LOGLEVEL --entitytype protein
#python src/main.py load_corpus --goldstd lll_train --log $LOGLEVEL --entitytype protein
#python src/main.py load_corpus --goldstd aimed_proteins --log $LOGLEVEL --entitytype protein
#python src/main.py load_corpus --goldstd bioinfer --log $LOGLEVEL --entitytype protein


#python src/main.py load_genia --goldstd lll_train --log $LOGLEVEL --entitytype protein
#python src/main.py load_genia --goldstd aimed_proteins --log $LOGLEVEL --entitytype protein
#python src/main.py load_genia --goldstd jnlpba_train --log $LOGLEVEL --entitytype protein
#python src/main.py load_genia --goldstd bc2gm_train --log $LOGLEVEL --entitytype protein
# python src/main.py load_genia --goldstd bioinfer --log $LOGLEVEL --entitytype protein

#python src/main.py train --goldstd jnlpba_train --log $LOGLEVEL --entitytype protein --models models/jnlpba_train_protein_crfsuite --crf crfsuite
#python src/main.py train --goldstd bc2gm_train --log $LOGLEVEL --entitytype protein --models models/bc2gm_train_protein_crfsuite --crf crfsuite
#python src/main.py train --goldstd lll_train --log $LOGLEVEL --entitytype protein --models models/lll_train_protein_crfsuite --crf crfsuite
#python src/main.py train --goldstd aimed_proteins --log $LOGLEVEL --entitytype protein --models models/aimed_protein_crfsuite --crf crfsuite
#python src/main.py train --goldstd miRNACorpus_train --log $LOGLEVEL --entitytype protein --models models/mirna_train_protein_crfsuite --crf crfsuite
python src/main.py train --goldstd miRTex_dev --log $LOGLEVEL --entitytype protein --models models/mirtex_train_protein_crfsuite --crf crfsuite

#python src/main.py train --goldstd jnlpba_train --log $LOGLEVEL --entitytype protein --models models/jnlpba_train_protein_sner --crf stanford
#python src/main.py train --goldstd bc2gm_train --log $LOGLEVEL --entitytype protein --models models/bc2gm_train_protein_sner --crf stanford
#python src/main.py train --goldstd lll_train --log $LOGLEVEL --entitytype protein --models models/lll_train_protein_sner --crf stanford
#python src/main.py train --goldstd aimed_proteins --log $LOGLEVEL --entitytype protein --models models/aimed_protein_sner --crf stanford
#python src/main.py train --goldstd miRNACorpus_train --log $LOGLEVEL --entitytype protein --models models/mirna_train_protein_sner --crf stanford
python src/main.py train --goldstd miRTex_dev --log $LOGLEVEL --entitytype protein --models models/mirtex_train_protein_sner --crf stanford
