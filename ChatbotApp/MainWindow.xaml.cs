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
        private MainWindowViewModel viewModel;

        public MainWindow()
        {
            InitializeComponent();
            viewModel = new MainWindowViewModel();
            this.DataContext = viewModel;
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
                    viewModel.SendMessage(null);
                }
            }
        }

        private void SendButton_Click(object sender, RoutedEventArgs e)
        {
            viewModel.SendMessage(null);
        }

        // Removed ScrollToBottom and all code referencing MessagesPanel

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

            // Update theme resources
            var themeDictionary = new ResourceDictionary();
            if (isDarkTheme)
            {
                // Load dark theme
                themeDictionary.Source = new Uri("Styles/DarkTheme.xaml", UriKind.Relative);
            }
            else
            {
                // Load light theme
                themeDictionary.Source = new Uri("Style/LightTheme.xaml", UriKind.Relative);
            }
            Application.Current.Resources.MergedDictionaries.Clear();
            Application.Current.Resources.MergedDictionaries.Add(themeDictionary);
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

        protected override void OnClosed(EventArgs e)
        {
            viewModel?.Dispose();
            base.OnClosed(e);
        }
    }
}