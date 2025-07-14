using System;
using System.Windows;
using System.Windows.Input;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Animation;

namespace ChatbotApp
{
    public partial class MainWindow : Window
    {
        private bool isDarkTheme = true;

        public MainWindow()
        {
            InitializeComponent();
            this.DataContext = new MainWindowViewModel();
            
            // Set placeholder text
            SetPlaceholderText();
            
            // Auto-scroll to bottom
            ScrollToBottom();
        }

        private void SetPlaceholderText()
        {
            if (MessageTextBox.Text == "")
            {
                MessageTextBox.Text = "Type your message...";
                MessageTextBox.Foreground = new SolidColorBrush(Color.FromRgb(161, 161, 161));
            }
        }

        private void MessageTextBox_GotFocus(object sender, RoutedEventArgs e)
        {
            if (MessageTextBox.Text == "Type your message...")
            {
                MessageTextBox.Text = "";
                MessageTextBox.Foreground = new SolidColorBrush(Colors.White);
            }
        }

        private void MessageTextBox_LostFocus(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(MessageTextBox.Text))
            {
                SetPlaceholderText();
            }
        }

        private void MessageTextBox_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter)
            {
                if (Keyboard.Modifiers == ModifierKeys.Shift)
                {
                    // Allow new line with Shift+Enter
                    return;
                }
                else
                {
                    // Send message with Enter
                    e.Handled = true;
                    SendMessage();
                }
            }
        }

        private void SendButton_Click(object sender, RoutedEventArgs e)
        {
            SendMessage();
        }

        private void SendMessage()
        {
            var message = MessageTextBox.Text;
            if (string.IsNullOrWhiteSpace(message) || message == "Type your message...")
                return;

            // Add user message to chat
            AddUserMessage(message);

            // Clear input
            MessageTextBox.Text = "";
            SetPlaceholderText();

            // Simulate AI response (you'll replace this with your backend integration)
            SimulateAIResponse(message);
        }

        private void AddUserMessage(string message)
        {
            var userMessage = CreateMessageBubble(message, true);
            MessagesPanel.Children.Add(userMessage);
            ScrollToBottom();
        }

        private void AddAIMessage(string message)
        {
            var aiMessage = CreateMessageBubble(message, false);
            MessagesPanel.Children.Add(aiMessage);
            ScrollToBottom();
        }

        private Border CreateMessageBubble(string message, bool isUser)
        {
            var border = new Border
            {
                Background = isUser ? 
                    new SolidColorBrush(Color.FromRgb(59, 130, 246)) : 
                    new SolidColorBrush(Color.FromRgb(45, 45, 45)),
                CornerRadius = isUser ? 
                    new CornerRadius(12, 12, 4, 12) : 
                    new CornerRadius(12, 12, 12, 4),
                Padding = new Thickness(16, 12, 16, 12),
                Margin = isUser ? 
                    new Thickness(80, 0, 0, 16) : 
                    new Thickness(0, 0, 80, 16),
                HorizontalAlignment = isUser ? 
                    HorizontalAlignment.Right : 
                    HorizontalAlignment.Left,
                Effect = new System.Windows.Media.Effects.DropShadowEffect
                {
                    Color = Colors.Black,
                    Direction = 270,
                    ShadowDepth = 1,
                    BlurRadius = 6,
                    Opacity = 0.1
                }
            };

            var stackPanel = new StackPanel();

            var messageText = new TextBlock
            {
                Text = message,
                FontFamily = new FontFamily("Segoe UI"),
                FontSize = 14,
                LineHeight = 20,
                Foreground = isUser ? 
                    new SolidColorBrush(Colors.White) : 
                    new SolidColorBrush(Colors.White),
                TextWrapping = TextWrapping.Wrap
            };

            var timestamp = new TextBlock
            {
                Text = DateTime.Now.ToString("HH:mm"),
                FontFamily = new FontFamily("Segoe UI"),
                FontSize = 11,
                Foreground = isUser ? 
                    new SolidColorBrush(Color.FromArgb(176, 255, 255, 255)) : 
                    new SolidColorBrush(Color.FromRgb(161, 161, 161)),
                HorizontalAlignment = HorizontalAlignment.Right,
                Margin = new Thickness(0, 8, 0, 0)
            };

            stackPanel.Children.Add(messageText);
            stackPanel.Children.Add(timestamp);
            border.Child = stackPanel;

            // Add fade-in animation
            border.Opacity = 0;
            border.RenderTransform = new TranslateTransform(0, 20);
            
            var fadeIn = new DoubleAnimation(0, 1, TimeSpan.FromMilliseconds(300));
            var slideUp = new DoubleAnimation(20, 0, TimeSpan.FromMilliseconds(300));
            
            border.BeginAnimation(OpacityProperty, fadeIn);
            border.RenderTransform.BeginAnimation(TranslateTransform.YProperty, slideUp);

            return border;
        }

        private void SimulateAIResponse(string userMessage)
        {
            // Simulate typing delay
            var timer = new System.Windows.Threading.DispatcherTimer();
            timer.Interval = TimeSpan.FromMilliseconds(1000);
            timer.Tick += (s, e) => {
                timer.Stop();
                
                // Generate a sample response based on input
                string response = GenerateSampleResponse(userMessage);
                AddAIMessage(response);
            };
            timer.Start();
        }

        private string GenerateSampleResponse(string userMessage)
        {
            // Simple response generator for demo purposes
            var responses = new string[]
            {
                "I understand your question. Let me help you with that.",
                "That's an interesting point. Here's what I think about it...",
                "I can definitely assist you with that. Let me provide you with some information.",
                "Thank you for your question. Based on what you've asked, I would suggest...",
                "I'm here to help! Let me break this down for you step by step."
            };

            var random = new Random();
            return responses[random.Next(responses.Length)];
        }

        private void ScrollToBottom()
        {
            ChatScrollViewer.ScrollToBottom();
        }

        private void VoiceButton_Click(object sender, RoutedEventArgs e)
        {
            // Implement voice input functionality
            MessageBox.Show("Voice input feature will be implemented here.");
        }

        private void AttachButton_Click(object sender, RoutedEventArgs e)
        {
            // Implement file attachment functionality
            MessageBox.Show("File attachment feature will be implemented here.");
        }

        private void SettingsButton_Click(object sender, RoutedEventArgs e)
        {
            // Implement settings window
            MessageBox.Show("Settings panel will be implemented here.");
        }

        private void ThemeToggleButton_Click(object sender, RoutedEventArgs e)
        {
            // Toggle between dark and light themes
            isDarkTheme = !isDarkTheme;
            
            // Update theme resources (you can implement light theme resources)
            if (isDarkTheme)
            {
                // Load dark theme
                var darkTheme = new ResourceDictionary();
                darkTheme.Source = new Uri("Styles/DarkTheme.xaml", UriKind.Relative);
                Application.Current.Resources.MergedDictionaries.Clear();
                Application.Current.Resources.MergedDictionaries.Add(darkTheme);
            }
            else
            {
                // Load light theme (implement LightTheme.xaml if needed)
                MessageBox.Show("Light theme will be implemented in LightTheme.xaml");
            }
        }

        private void MinimizeButton_Click(object sender, RoutedEventArgs e)
        {
            this.WindowState = WindowState.Minimized;
        }

        private void CloseButton_Click(object sender, RoutedEventArgs e)
        {
            this.Close();
        }

        private void TitleBar_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.LeftButton == MouseButtonState.Pressed)
            {
                this.DragMove();
            }
        }
    }
}