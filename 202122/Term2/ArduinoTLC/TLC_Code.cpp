// Rafferty Simms - N0990815

/* DECLARATION OF OWNERSHIP ----------------------------------------------

1. I am aware of the University’s rules on plagiarism and collusion and I understand
that, if I am found to have broken these rules, it will be treated as Academic
Misconduct and dealt with accordingly. I understand that if I lend this piece of work
to another student and they copy all or part of it, either with or without my
knowledge or permission, I shall be guilty of collusion.

2. In submitting this work I confirm that I am aware of, and am abiding by, the
University’s expectations for proof-reading.

3. I understand that I must submit this coursework by the time and date published. I
also understand that if this coursework is submitted late it will, if submitted within 5
working days of the deadline date and time, be given a pass mark as a maximum
mark. If received more than 5 working days after the deadline date and time, it will
receive a mark of 0%. For referred or repeat coursework, I understand that if the
coursework is not submitted by the published date and time, a mark of 0% will be
automatically awarded.

4. I understand that it is entirely my responsibility to ensure that I hand in my full and
complete coursework and that any missing pages handed in after the deadline will
be disregarded.

5. I understand that the above rules apply even in the eventuality of computer or
other information technology failures.

*/

int mode = 49;
int button_pressed = false;

// CLASSES ---------------------------------------------------------------


class OutputComponent // Base abstract class for a component that can be turned on or off
{
public:
    OutputComponent(int pin) // initalise object with the pin value that was passed in
    {
        this->pin = pin;
        pinMode(pin, OUTPUT);
    }
    virtual void on() = 0;
    virtual void off() = 0;
protected:
    int pin;
};

class Light : public OutputComponent // Light class derived from OutputComponent implementing the respective methods to turn the LED related to the specified pin on or off
{
public:
    Light(int pin) : OutputComponent(pin) {}
    void on() // method to turn the LED on
    {
        digitalWrite(this->pin, HIGH);
    }
    void off() // method to turn the LED off
    {
        digitalWrite(this->pin, LOW);
    }
};

class Buzzer : public OutputComponent  // Buzzer class derived from OutputComponent implementing the respective methods to turn the buzzer related to the specified pin on or off
{
public:
    Buzzer(int pin) : OutputComponent(pin) {}
    void on() // method to turn the buzzer on
    {
        tone(this->pin, HIGH);
    }
    void off() // method to turn the buzzer off
    {
        noTone(this->pin);
    }
};

class DistanceSensor // DistanceSensor class used to get the value of objects from a distance sensor attached at the specified pins
{
private:
    int trigPin;
    int echoPin;

public:
    DistanceSensor(int trigPin, int echoPin) // initialise the object with the specified TRIG and ECHO pins
    {
        this->trigPin = trigPin;
        this->echoPin = echoPin;
        pinMode(trigPin, OUTPUT);
        pinMode(echoPin, INPUT);
    }

    /*
        Return distance of the closest object within the
        range of the Ultrasonic Distance Sensor
    */
    long getDistance() // method used to return the distance of an/the object from the ultrasonic distance sensor
    {
        digitalWrite(this->trigPin, LOW);
        delayMicroseconds(2);
        digitalWrite(this->trigPin, HIGH);
        delayMicroseconds(5);
        digitalWrite(this->trigPin, LOW);
        long centimeters = pulseIn(this->echoPin, HIGH) / 29 / 2;
        return centimeters;
    }
};

class LightSensor // LightSensor class used to get the value of the attached LDR
{
private:
    int pin;

public:
    LightSensor(int pin) // initialise object with the specified PIN related to the LDR
    {
        this->pin = pin;
        pinMode(pin, INPUT);
    }

    int getValue() // return the light level reading of the Photoresistor (LDR)
    {
        unsigned int sensorValue = analogRead(this->pin);
        return sensorValue * (5000.0 / 1024.0);
    }
};

Light green = Light(11); // initialise a Light object with the pin used for the green LED
Light yellow = Light(12); // initialise a Light object with the pin used for the yellow LED
Light red = Light(13); // initialise a Light object with the pin used for the red LED

Buzzer buzzer = Buzzer(10); // initialise a Buzzer object with the pin used for the buzzer
DistanceSensor distanceSensor = DistanceSensor(6, 7); // initialise a DistanceSensor object with the pins used for the TRIG and ECHO pins respectively 
LightSensor lightSensor = LightSensor(A0); // initialise a LightSensor object with the analog pin used for the LDR

// SETUP FUNCTION ------------------------------------------------------------

void setup()
{
    Serial.begin(9600);
    pinMode(2, INPUT); // set the mode of pin 2 to INPUT, this is the pin used for the push button and is a pin which an interrupt can be attached to
}

// DEFAULT MODES -------------------------------------------------------------

/*
    Executes regular mode

    - Display red light for 2 seconds
    - Display yellow light for 1 second
    - Display green light for 2 seconds
    - Display yellow light for 1 second
*/
void regularMode()
{
    red.on(); // red on for 2 seconds
    delay(2000);
    red.off();
    yellow.on(); // yellow on for 1 second
    delay(1000);
    yellow.off();
    green.on(); // green on for 2 seconds
    delay(2000);
    green.off();
    yellow.on(); // yellow on for 1 second
    delay(1000);
    yellow.off();
}

/*
    Executes pedestrian mode

    - If an object is within 10cm of the proximity sensor
        - Turn the buzzer on
        - Flash the yellow light on and off 10 times
        - Turn the buzzer off
    - If there are no objects within 10cm of the proximity sensor
        - Execute regular mode
*/
void pedestrianMode()
{
    if (distanceSensor.getDistance() < 10) // if the distance from the ultrasonic distance sensor is below 10 centimeters
    {
        buzzer.on(); // turn on the buzzer
        for (int i = 0; i < 10; i++) // loop 10 times
        {
            yellow.on(); // turn on the yellow light for a tenth of a second
            delay(100);
            yellow.off(); // turn off the yellow light for a tenth of a second
            delay(100);
        }
    }
    else // if the distance from the ultrasonic distance sensor is above 10 centimeters
    {
        regularMode(); // execut regular mode
    }
    buzzer.off();
}

/*
    Executes night mode

   - If the light level is below 3000
        - If an object is within 10cm of the proximity sensor
            - Turn on the green light
        - If there are no objects within 10cm of the proximity sensor
            - Turn on the red light
   - If the light level is above 3000
        - Execute regular mode
*/
void nightMode()
{
    if (lightSensor.getValue() < 3000) // if the light sensor value is below 3000
    {
        if (distanceSensor.getDistance() < 10) // if the distance from the ultrasonic distance sensor is below 10 centimeters
        {
            red.off(); // turn off the redlight
            green.on(); // turn on the greenlight
        }
        else // if the distance from the ultrasonic distance sensor is above 10 centimeters
        {
            green.off(); // turn off the greenlight
            red.on(); // turn on the redlight
        }
    }
    else // if the light sensor value is above 3000
    {
        green.off(); // turn off the green light
        red.off(); // turn off the redlight
        regularMode(); // execute regular mode
    }
}

// ADDITIONAL MODES -----------------------------------------------------------

/*
    Executes manual mode

    - If the push button is pressed
        - Display the yellow light for 1 second
        - Turn on the buzzer
        - Display the red light for 10 seconds
        - Turn off the buzzer
    - Otherwise a green light will be displayed until the button is pushed
*/
void manualMode()
{
    if (!button_pressed) // if the button has not been pressed within the last iteraction
    {
        green.on(); // keep the greenlight on
    }
    else // if the button has been pressed
    {
        green.off(); // turn off the greenlight
        yellow.on(); // turn on the yellow light for 1 second
        delay(1000);
        yellow.off();
        buzzer.on(); // turn on the buzzer for 10 seconds
        red.on(); // turn on the red light for 10 seconds
        delay(10000);
        buzzer.off();
        red.off();
        yellow.on(); // turn on the yellow light for 1 second
        delay(1000);
        yellow.off();
        button_pressed = false; // reset the button pressed boolean value
    }
}

/*
    Interrupt to be attached to the push button when manual mode is active

    When the button is pressed, the button_pressed value will be set to true if it is not already.
*/

void pushButtonManualModeInterrupt()
{
    if (!button_pressed)
    {
        button_pressed = true;
    }
}

// MAIN LOOP ------------------------------------------------------------------

void loop()
{

    /*
        Mode Selection Input

        1 - Regular
        2 - Pedestrian
        3 - Night
    */

    if (Serial.available() > 0)
    {
        int input = Serial.read(); // read the input value from the serial
        if (input == 50 || input == 51 || input == 49 || input == 52) // if the input value relates to a valid mode (input is either the character 1, 2 ,3 or 4)
        {
            if (input != mode) { // if the input mode is different to the mode that is currently being executed
                red.off(); // turn off all lights
                green.off();
                yellow.off();
                if (input == 52 && mode != 52) // if the input option is manual mode
                {
                    attachInterrupt(digitalPinToInterrupt(2), pushButtonManualModeInterrupt, FALLING); // attach an interrupt to the push button
                }
                else if (mode == 52 && input != 52) // if the input option is not manual mode and the previously executed mode is manual mode
                {
                    detachInterrupt(digitalPinToInterrupt(2)); // detach the interrupt from the push button so that it will not interrupt other modes
                }
                mode = input; // set the current mode to whichever was input
            }

        }
    }


    Serial.print("MODE: ");
    switch (mode) // switch statement to execute the function relative to the current mode value
    {
    case 50: // if the input was "2", the mode is pedestrian
        Serial.println("Pedestrian");
        pedestrianMode(); // execute the pedestrian mode function
        break;
    case 51: // if the input was "3", the mode is night
        Serial.println("Night");
        nightMode(); // execute the night mode function
        break;
    case 52: // if the input was "4", the mode is manual
        Serial.println("Manual");
        manualMode(); // execute the manual mode function
        break;
    default: // defaults to regular mode if value "1" is input or an invalid value is input before the mode changes
        Serial.println("Regular");
        regularMode(); // execute the regular mode function
        break;
    }
}
