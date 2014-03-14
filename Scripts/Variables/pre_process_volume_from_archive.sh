#!/bin/bash
export LC_ALL=$LANG
export HOCR="ABBYY" 
export RIGAUDON_HOME=`pwd`
export FBEVALUATOR_HOME=$RIGAUDON_HOME/OpenGreekAndLatin/bin/fbevaluator
export GAMERA_CMDS=" --split --autogroup  --filter --otsu  0.94,0.97,1.0,1.03,1.05,1.07,1.09,1.12,1.15,1.17"
export ARCHIVE_ID=septemadthebased00aescuoft
export CLASSIFIER_DIR=$RIGAUDON_HOME/Gamera/Classifiers/Kaibel_Round_4/
export TEXT_STAGING_DIR=$RIGAUDON_HOME/OCR_Processing/Texts

export PROCESSING_DIR=$TEXT_STAGING_DIR/$ARCHIVE_ID
export DICTIONARY_FILE=$RIGAUDON_HOME/Dictionaries/combined_good.txt

#Set the directories for the outputs of Sun Grid Engine
export OUTPUT_DIR=$RIGAUDON_HOME/OCR_Processing/Logs/sge_out
export ERROR_DIR=$RIGAUDON_HOME/OCR_Processing/Logs/sge_errors

$RIGAUDON_HOME/Scripts/process_volume_from_archive.sh
