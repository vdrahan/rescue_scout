# Project Information

**FIRST NAME LAST NAME:** Vladyslav Drahan  

**Sparring Partner:** Vsevolod Bereza  

**Project Title:** RC CAR search-and-rescue system - version 2    

**Project Summary in max 10 words:** 
AI-powered RC car helps rescuers detect people in dangerous environments.  

# Tips for Feedback Conversations

## Preparation

> Determine for yourself what you would like feedback on. Write down a few points in advance where you definitely want to receive feedback. This way, the feedback conversation will be more focused and the questions you definitely want answered will be addressed.

## During the Conversation:

> **Listen actively:** Do not immediately go on the defensive but try to listen well. Show both verbally and non-verbally that you are paying attention to the feedback by maintaining an open posture (eye contact, upright posture), taking notes, nodding...

> **Take notes:** Write down the feedback so you have it later. Note the key words and find a quick notation method for yourself. If you take good notes, you can briefly review your main feedback points at the end of the conversation.

> **Summarize:** Do not wait for a summary from the instructors, this is your task: Check if you have understood the message correctly by actively listening and summarizing in your own words.

> **Be open to the feedback:** Do not wait for a summary from the instructors, this is your task: Check if you have understood the message correctly by actively listening and summarizing in your own words.

> **Think about it:** Consider what you are going to do with the feedback and follow up. Do you find the comments justified or unjustified? Do you recognize yourself in the feedback? How are you going to address this?

## AFTER THE CONVERSATION

> Reread your notes and create action points. Make choices from all the feedback you received: What can you work on and what will you set aside for now. What were the priorities? Review the assignment sheet again to determine your focus points. Write your action points on the feedback sheet.

# Feedforward Conversations

## Conversation 1 (Date: 28/05/2026)

Lecturer: Tijn VERAGHTERT 

Questions for this conversation:

- Question 1: What changes need to be made to the 3D-printed camera mount module?

- Question 2: What changes need to be made to the nameplate?

- Question 3: Will 3 mm ABS plastic be suitable for making the enclosure?

This is the feedback on my questions.

- Feedback 1: Add mounting holes on the side that will be attached to the RC car. The holes should be slightly smaller than the screw diameter so the screws can grip the material properly.

- Feedback 2: 1. The letter width is too small for laser cutting. Instead, cut the plate shape and engrave the letters onto it. 2. Remove the duplicated red lines.

- Feedback 3: 3 mm ABS plastic should work well for the enclosure of this project.


## Conversation 2 (Date: 28/05/2026)

Lecturer: Marie DEWITTE

Questions for this conversation:

- Question 1: Is the night camera mode worth implementing?

This is the feedback on my questions.

- Feedback 1: The night camera mode is worth implementing because it would be an impressive and useful addition to the system.



## Conversation 3 (Date: 29/05/2026)

Lecturer: Tijn VERAGHTERT

Questions for this conversation:

- Question 1: Is the updated version of the camera module printable?

This is the feedback on my questions.

- Feedback 1: The new updated version is almost production-ready. The position of the mounting holes and the overall dimensions are correct. However, a few small adjustments are still needed: 1. Make the mounting side smaller so the slope angle can be reduced. 2. Make the space for the camera stick slightly wider and adjust the wall thickness accordingly.

## MVP1 (Date: 02/06/2026)

Lecturer: Marie Dewitte, Frederiek Berthier, Christophe Laprudence, Dieter Roobrouck

* **Model & Dataset Feedback:**

    1. Indoor performance

        The model performance is not stable when detecting different people indoors. This is likely because the dataset was collected mostly outdoors and contains many images of the same people wearing similar clothes. To improve the model, more data should be collected with different people, different clothing, and different environments, including indoor locations.

    2. Class imbalance

        The dataset is strongly imbalanced, especially for the crawling_person class. To fix this, more samples should be collected for the underrepresented classes.

    3. Model choice

        The current model choice should be reconsidered. It may be better to switch to a newer YOLO version - YOLOv26, it is better optimized for working on a Raspberry Pi.
     

* **UI Design Feedback :**
    1. 
        The current UI design does not look very professional. The theme should be less colorful and more consistent, with a cleaner and more balanced visual style.
    2. 
        Use Buttons instead of scrolling, it will make the usage of touchscreen display more convenient 


## Conversation 4 (Date: 03/06/2026)

Lecturer: Pieter-Jan BEECKMAN

Questions for this conversation:

- Question 1: How the hardware should be assembled ?

This is the feedback on my questions.

**Feedback:**
  
1. LEDs

    The LEDs should be connected to the Raspberry Pi using GPIO and GND pins. Each LED should have a resistor connected in series on the GPIO side to limit the current.

2. Gas sensor

    The gas sensor should use two 1kΩ resistors as a voltage divider. The signal wire should be connected between the two resistors. The second resistor should then be connected to GND, and this GND should go back to the Raspberry Pi.

3. Active buzzer

    The positive wire of the active buzzer should be connected to a GPIO pin, and the negative wire should be connected to GND.

4. RGB LED module, DHT11, and LCD

    The RGB LED module, DHT11 sensor, and LCD can be connected directly to the Raspberry Pi using their required power, ground, signal, and communication pins.


## Conversation 5 (Date: 04/06/2026)

Lecturer: Tijn VERAGHTERT

Questions for this conversation:

- Question 1: Does nameplate file require any adjustments?

This is the feedback on my questions.

- Feedback 1: Only minor adjustments to the line colors are needed. Once this is done, the nameplate can be approved for laser cutting, it has a GO.


    +## MVP2 (Date: 09/06/2026)

Lecturer: Claudia EECKHOUT, Pieter-Jan BEECKMAN, Paula ACUÑA RONCANCIO

* **Model & Dataset Feedback:**

    1. Misclassification and missed detections

        The model still shows unstable detection performance. It sometimes assigns the wrong class to a person or fails to detect the person completely.

    2. Class imbalance

        The dataset is still imbalanced, which causes the model to perform better on majority classes and worse on minority classes. To improve this, more samples should be collected for the underrepresented classes.
    
    3. Reducing false negatives
        
        Further tuning is needed to reduce false negatives, since the system should prioritize detecting a person over avoiding false alarms.

    4. Dataset diversity
        
        The dataset should be expanded with images of people with different appearances, including skin color, gender, height, body type, clothing, and poses.


* **Gradio:**

    1. Debugging Page

        A debugging page should be implemented to monitor the system status and verify that each connected component is working correctly.

* **General recommendation:**

    1. Train before presenting

        Before the Tourmoment, it is useful to practise pronunciation and rehearse the product pitch to make sure the concept, features, and purpose of the product can be explained clearly.

## Conversation 6 (Date: 04/06/2026)

Lecturer: Geert DESLOOVERE

Questions for this conversation:

- Question 1: How to connect the MQ-2 gas sensor to the Raspberry Pi?

This is the feedback on my questions.

- Feedback 1: To connect the MQ-2 sensor to the Raspberry Pi, an ADC converter is required because the Raspberry Pi cannot read analog signals directly.

The A0 pin of the MQ-2 sensor should be connected to the analog input pin of the ADC.

From the ADC, the connections should be made as follows:

- VCC connects to the 5V power pin on the Raspberry Pi.
- SDA connects to the Raspberry Pi SDA pin.
- SCL connects to the Raspberry Pi SCL pin.
- GND connects to the GND of the MQ-2 sensor and then to a GND pin on the Raspberry Pi.

## MVP3 (Date: 09/06/2026)

Lecturer: Stijn Walcarius , Geert DESLOOVERE, Thomas Huyghebaert

* ** Techconnect Template **

    The 


## Conversation 7 (Date: 04/06/2026)

Lecturer: MArie DEWITTE

Questions for this conversation:

- Question 1: How to connect the MQ-2 gas sensor to the Raspberry Pi?

This is the feedback on my questions.

- Feedback 1: To connect the MQ-2 sensor to the Raspberry Pi, an ADC converter is required because the Raspberry Pi cannot read analog signals directly.