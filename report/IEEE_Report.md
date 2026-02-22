# Voronoi-Based Node Scheduling in Wireless Sensor Networks
**Author:** Om Seth  
**Date:** 2026-02-22

## Abstract
Dense WSN deployments contain redundancy, wasting energy. This project uses bounded Voronoi areas to identify redundant nodes and schedule them OFF while maintaining coverage. OFF nodes become backups for fault tolerance. A full-stack dashboard visualizes results and compares against random baselines.

## Keywords
WSN, Voronoi, Scheduling, Coverage, Energy, Fault tolerance

## Method
Threshold: A_th = k * pi * R_s^2. Iteratively OFF the node with smallest bounded Voronoi area if below A_th.

## Fault tolerance
Random failures + greedy backup activation if coverage drops.

## Dashboard
Run, Compare, Experiments (Energy vs Density), CSV exports.
