#!/bin/bash

echo "\$kubectl get vpa ${1} --no-headers -o \"custom-columns=:status.recommendation.containerRecommendations[0].target.cpu\""
kubectl get vpa ${1} --no-headers -o "custom-columns=:status.recommendation.containerRecommendations[0].target.cpu"
echo -e "\n"