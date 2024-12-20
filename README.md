# Human Factors Project 2024-2025

This repository contains the implementation of the **Human Factors Project** as outlined in the subject document for the 2024-2025 academic year under the guidance of Prof. F. Vanderhaegen. The project explores perceptual and attentional capacities during supervisory tasks with visual and auditory dynamic events.

## Project Objective

The goal is to simulate tasks involving control and supervision under dynamic conditions where events such as **flashing images and sounds** occur periodically or aperiodically in relation to participants' heart rate. The specific implementation chosen involves **guiding a mobile through a circuit** with three increasing levels of difficulty.

## Features

### Simulation Overview

- **Three Levels of Difficulty**:
  - **Level 1**: Simple paths with minimal directional changes.
  - **Level 2**: Moderate complexity with more frequent directional changes.
  - **Level 3**: Complex paths requiring constant navigation and direction changes.

- **Event Handling**:
  - Flashing images and sounds act as "bonus points" that participants must click to progress faster.
  - Visual and auditory alarms that demand timely participant responses.

- **Participant Interaction**:
  - Participants control the mobile using keyboard arrow keys or on-screen buttons.
  - Images appear and flash for 5 seconds at predefined locations, requiring participant clicks.

### Experimental Conditions

Three experimental conditions are simulated, requiring 20 participants per condition:
1. **Periodic Synchronous**: Flashing images and sounds are synchronized in real-time with participants' heart rate.
2. **Periodic Asynchronous**: Fixed heart rate of 100 BPM (participants with 100 BPM heart rates are excluded).
3. **Aperiodic**: Flashing events are based on heart rate but occur at random intervals.

### Participant Feedback
At the end of each level, participants evaluate:
- **Performance**: Rated on a scale (Very Low - Very High).
- **Stress Level**: Rated on a scale (Very Low - Very High).
- **Certainty**: Confidence in their evaluations (Not Sure - Moderately Sure - Very Sure).

### Data Collection
The following data points are recorded:
- Age and gender of participants.
- Heart rate before and after the experiment.
- Reaction times to events.
- Non-responses to events.
- Self-evaluations of performance, stress, and certainty.

