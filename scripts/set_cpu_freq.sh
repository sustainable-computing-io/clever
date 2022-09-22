#!/bin/bash

FREQ=${1}
cpupower frequency-set -d ${FREQ}
cpupower frequency-set -u ${FREQ}