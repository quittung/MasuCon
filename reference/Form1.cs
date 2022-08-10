using System;
using System.Windows.Forms;
using ScpDriverInterface;
using System.IO.Ports;
using System.Runtime.InteropServices;

namespace WindowsFormsApplication1
{
    public partial class Form1 : Form
    {
        ScpBus scpBus;
        X360Controller controller;

        SerialPort arduino;

        int currentNotch, targetNotch;

        Timer t;
        bool busy;

        string logText = "";


        [DllImport("user32.dll")]
        private extern static IntPtr SetActiveWindow(IntPtr handle);
        private const int WM_ACTIVATE = 6;
        private const int WA_INACTIVE = 0;

        IntPtr LastWindowHandle = IntPtr.Zero;

        public Form1()
        {
            Log("setting up emulated Xbox controller");
            scpBus = new ScpBus();
            scpBus.PlugIn(2); //TODO: Make this user defined
            Log("registered as controller 2");
            controller = new X360Controller();


            arduino = findDevice("masucon");
            if (arduino == null)
            {
                Log("could not find arduino, aborting");
                MessageBox.Show("Could not connect to MasuCon");
                Environment.Exit(1);
            }
            arduino.DataReceived += Arduino_DataReceived;

            InitializeComponent();

            // Define the border style of the form to a dialog box.
            this.FormBorderStyle = FormBorderStyle.FixedDialog;

            // Set the start position of the form to the center of the screen.
            this.StartPosition = FormStartPosition.CenterScreen;

            Log("done");

            t = new Timer();
            t.Interval = 5;
            t.Tick += T_Tick;
            t.Start();
        }

        private SerialPort findDevice(string id)
        {
            Log("scanning for masucon on serial ports");
            var comPorts = SerialPort.GetPortNames();
            foreach (var portName in comPorts)
            {
                SerialPort comPort;
                try
                {
                    comPort = new SerialPort(portName, 9600);
                    comPort.NewLine = "\r\n";
                    comPort.Open();
                }
                catch (UnauthorizedAccessException)
                {
                    Log("port " + portName + " could not be opened.");
                    continue;
                }
                if (comPort.IsOpen)
                {
                    comPort.ReadTimeout = 500;
                    comPort.Write("id\r");
                    try
                    {
                        if (comPort.ReadLine() == id)
                        {
                            Log("found MasuCon on port " + portName);
                            return comPort;
                        }
                        else
                            Log("could not identify device on port " + portName);
                    }
                    catch (TimeoutException)
                    {
                        Log("no response on port " + portName);
                    }
                }
                else
                {
                    Log(portName + " is not open");
                }

                //clean up
                if (comPort.IsOpen)
                    comPort.Close();
                comPort.Dispose();
            }

            return null;
        }

        private void T_Tick(object sender, EventArgs e)
        {
            updateNotch();
        }

        void Log(string s)
        {
            Console.WriteLine(s);
            logText += s + "\r\n";

            if (textBox1 != null)
                textBox1.Text = logText;
        }

        private void Arduino_DataReceived(object sender, SerialDataReceivedEventArgs e)
        {
            var telegram = arduino.ReadLine();
            targetNotch = Convert.ToInt32(telegram);

            // remap controller position
            int pMax = (int)nUDpMax.Value;
            int bMax = (int)nUDbMax.Value;
            int bEB = (int)nUDbEB.Value;

            if (targetNotch > pMax)
                targetNotch = pMax;
            if (targetNotch < bMax && targetNotch > bEB)
                targetNotch = bMax;
            if (targetNotch <= bEB)
                targetNotch = bMax - 1;

            //Console.WriteLine(targetNotch);
        }


        /// <summary>
        /// Converts a notch to the equivalent string
        /// </summary>
        /// <param name="notch"></param>
        /// <returns></returns>
        string NotchToText(int notch)
        {
            int bEB = (int)nUDbMax.Value - 1;

            if (notch <= bEB)
                return "EB";
            else if (notch < 0)
                return "B" + (-notch);
            else if (notch == 0)
                return "N";
            else 
                return "P" + notch;
        }

        /// <summary>
        /// Helper for sending a specific button press to the sim
        /// </summary>
        /// <param name="button"></param>
        void sendButtonPress(X360Buttons button, bool refocus = false)
        {
            // Set time to wait for sim to register button press in ms
            const int pressTime = 20;
            const int waitTime = 50;

            // Activate last focused window
            if (refocus)
                SetActiveWindow(LastWindowHandle);

            // Send button press
            controller.Buttons |= button;
            scpBus.Report(2, controller.GetReport());
            System.Threading.Thread.Sleep(pressTime);

            // Send button release
            controller.Buttons &= ~button;
            scpBus.Report(2, controller.GetReport());
            System.Threading.Thread.Sleep(waitTime);
        }       

        /// <summary>
        /// Tries to move the game masucon to the position of the trackbar
        /// </summary>
        void updateNotch()
        {
            if (busy)
                return;
            else
                busy = true;
            

            label4.Text = NotchToText(currentNotch);
            label2.Text = NotchToText(targetNotch);

            while (targetNotch != currentNotch)
            {
                stepANotch(ref currentNotch, currentNotch < targetNotch);

                label2.Text = NotchToText(targetNotch);
                label4.Text = NotchToText(currentNotch);
                this.Invalidate();
                Application.DoEvents();
            }

            label2.Text = NotchToText(targetNotch);
            label4.Text = NotchToText(currentNotch);
            this.Invalidate();
            Application.DoEvents();

            busy = false;
        }
        
        /// <summary>
        /// Steps the game masucon up or down while using absolute notches if possible
        /// </summary>
        /// <param name="currentNotch">The assumed masucon position</param>
        /// <param name="up">Whether to step up or down</param>
        void stepANotch(ref int currentNotch, bool up)
        {
            // Find out what notch to step to
            int intendedNotch = currentNotch;
            if (up)
                intendedNotch++;
            else
                intendedNotch--;

            // Decide if the intended notch can be accessed via an absolute command
            switch (intendedNotch)
            {
                case -6:
                    sendButtonPress(X360Buttons.B);
                    currentNotch = -6;
                    break;
                case -1:
                    sendButtonPress(X360Buttons.Right);
                    currentNotch = -1;
                    break;
                case 0:
                    sendButtonPress(X360Buttons.Left);
                    currentNotch = 0;
                    break;
                default:
                    if (up)
                    {
                        sendButtonPress(X360Buttons.Down);
                        currentNotch++;
                    }
                    else
                    {
                        sendButtonPress(X360Buttons.Up);
                        currentNotch--;
                    }
                    break;
            }
        }
        
        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            scpBus.UnplugAll();
            scpBus.Dispose();
        }

        private void trackBar1_MouseUp(object sender, MouseEventArgs e)
        {
            //t1.Stop();
            //updateNotch(-trackBar1.Value);
            //t1.Start();

        }
        
        private void XButton_Click(object sender, EventArgs e)
        {
            if (sender == buttonUp)
                sendButtonPress(X360Buttons.Up, true);

            if (sender == buttonLeft)
                sendButtonPress(X360Buttons.Left, true);

            if (sender == buttonDown)
                sendButtonPress(X360Buttons.Down, true);

            if (sender == buttonRight)
                sendButtonPress(X360Buttons.Right, true);

            if (sender == buttonL1)
                sendButtonPress(X360Buttons.LeftBumper, true);

            if (sender == buttonR1)
                sendButtonPress(X360Buttons.RightBumper, true);

            if (sender == buttonSqu)
                sendButtonPress(X360Buttons.X, true);

            if (sender == buttonCro)
                sendButtonPress(X360Buttons.A, true);

            if (sender == buttonCir)
                sendButtonPress(X360Buttons.B, true);

            if (sender == buttonTri)
                sendButtonPress(X360Buttons.Y, true);

            if (sender == buttonStart)
                sendButtonPress(X360Buttons.Start, true);
        }

        private void trackBar1_ValueChanged(object sender, EventArgs e)
        {
            targetNotch = -trackBar1.Value;
            updateNotch();
        }
        
        protected override void WndProc(ref Message m)
        {
            if (m.Msg == WM_ACTIVATE)
            {
                if (((int)m.WParam & 0xFFFF) != WA_INACTIVE)
                {
                    LastWindowHandle = m.LParam;
                }
            }

            base.WndProc(ref m);
        }
    }
}
