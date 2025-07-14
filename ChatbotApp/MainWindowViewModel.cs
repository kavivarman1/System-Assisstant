using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows.Input;

namespace ChatbotApp
{
    public class MainWindowViewModel : INotifyPropertyChanged
    {
        private string _currentMessage;
        private bool _isTyping;
        private bool _isDarkTheme;

        public MainWindowViewModel()
        {
            Messages = new ObservableCollection<ChatMessage>();
            SendCommand = new RelayCommand(SendMessage, CanSendMessage);
            VoiceCommand = new RelayCommand(StartVoiceInput);
            AttachCommand = new RelayCommand(AttachFile);
            SettingsCommand = new RelayCommand(OpenSettings);
            ThemeToggleCommand = new RelayCommand(ToggleTheme);
            
            IsDarkTheme = true;
            
            // Add sample messages
            LoadSampleMessages();
        }

        public ObservableCollection<ChatMessage> Messages { get; }

        public string CurrentMessage
        {
            get => _currentMessage;
            set
            {
                _currentMessage = value;
                OnPropertyChanged();
                ((RelayCommand)SendCommand).RaiseCanExecuteChanged();
            }
        }

        public bool IsTyping
        {
            get => _isTyping;
            set
            {
                _isTyping = value;
                OnPropertyChanged();
            }
        }

        public bool IsDarkTheme
        {
            get => _isDarkTheme;
            set
            {
                _isDarkTheme = value;
                OnPropertyChanged();
            }
        }

        public ICommand SendCommand { get; }
        public ICommand VoiceCommand { get; }
        public ICommand AttachCommand { get; }
        public ICommand SettingsCommand { get; }
        public ICommand ThemeToggleCommand { get; }

        private void LoadSampleMessages()
        {
            Messages.Add(new ChatMessage
            {
                Content = "Hello! I'm your AI Assistant. How can I help you today?",
                IsFromUser = false,
                Timestamp = DateTime.Now.AddMinutes(-5)
            });

            Messages.Add(new ChatMessage
            {
                Content = "Can you help me write a professional email?",
                IsFromUser = true,
                Timestamp = DateTime.Now.AddMinutes(-4)
            });

            Messages.Add(new ChatMessage
            {
                Content = "Of course! I'd be happy to help you write a professional email. Could you tell me:\n\n• Who you're writing to\n• The purpose of the email\n• Any specific points you want to include",
                IsFromUser = false,
                Timestamp = DateTime.Now.AddMinutes(-4)
            });
        }

        private bool CanSendMessage(object parameter)
        {
            return !string.IsNullOrWhiteSpace(CurrentMessage) && !IsTyping;
        }

        private void SendMessage(object parameter)
        {
            if (string.IsNullOrWhiteSpace(CurrentMessage))
                return;

            // Add user message
            Messages.Add(new ChatMessage
            {
                Content = CurrentMessage,
                IsFromUser = true,
                Timestamp = DateTime.Now
            });

            var userMessage = CurrentMessage;
            CurrentMessage = string.Empty;

            // Simulate AI response
            SimulateAIResponse(userMessage);
        }

        private async void SimulateAIResponse(string userMessage)
        {
            IsTyping = true;

            // Simulate processing delay
            await System.Threading.Tasks.Task.Delay(1500);

            // Generate response
            var response = GenerateAIResponse(userMessage);

            Messages.Add(new ChatMessage
            {
                Content = response,
                IsFromUser = false,
                Timestamp = DateTime.Now
            });

            IsTyping = false;
        }

        private string GenerateAIResponse(string userMessage)
        {
            // Simple response generator for demo purposes
            var responses = new string[]
            {
                "I understand your question. Let me help you with that.",
                "That's an interesting point. Here's what I think about it...",
                "I can definitely assist you with that. Let me provide you with some information.",
                "Thank you for your question. Based on what you've asked, I would suggest...",
                "I'm here to help! Let me break this down for you step by step.",
                "Great question! Here's how I would approach this problem...",
                "I can help you with that. Let me provide you with a detailed explanation.",
                "That's a thoughtful question. Here's my perspective on it..."
            };

            var random = new Random();
            return responses[random.Next(responses.Length)];
        }

        private void StartVoiceInput(object parameter)
        {
            // Implement voice input functionality
            // This would integrate with speech recognition APIs
            System.Windows.MessageBox.Show("Voice input feature will be implemented here.");
        }

        private void AttachFile(object parameter)
        {
            // Implement file attachment functionality
            System.Windows.MessageBox.Show("File attachment feature will be implemented here.");
        }

        private void OpenSettings(object parameter)
        {
            // Implement settings window
            System.Windows.MessageBox.Show("Settings panel will be implemented here.");
        }

        private void ToggleTheme(object parameter)
        {
            IsDarkTheme = !IsDarkTheme;
            // Theme switching logic would be implemented here
        }

        public event PropertyChangedEventHandler PropertyChanged;

        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }

    public class ChatMessage : INotifyPropertyChanged
    {
        private string _content;
        private bool _isFromUser;
        private DateTime _timestamp;

        public string Content
        {
            get => _content;
            set
            {
                _content = value;
                OnPropertyChanged();
            }
        }

        public bool IsFromUser
        {
            get => _isFromUser;
            set
            {
                _isFromUser = value;
                OnPropertyChanged();
            }
        }

        public DateTime Timestamp
        {
            get => _timestamp;
            set
            {
                _timestamp = value;
                OnPropertyChanged();
                OnPropertyChanged(nameof(TimeString));
            }
        }

        public string TimeString => Timestamp.ToString("HH:mm");

        public event PropertyChangedEventHandler PropertyChanged;

        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }

    public class RelayCommand : ICommand
    {
        private readonly Action<object> _execute;
        private readonly Func<object, bool> _canExecute;

        public RelayCommand(Action<object> execute, Func<object, bool> canExecute = null)
        {
            _execute = execute ?? throw new ArgumentNullException(nameof(execute));
            _canExecute = canExecute;
        }

        public event EventHandler CanExecuteChanged
        {
            add { CommandManager.RequerySuggested += value; }
            remove { CommandManager.RequerySuggested -= value; }
        }

        public bool CanExecute(object parameter)
        {
            return _canExecute?.Invoke(parameter) ?? true;
        }

        public void Execute(object parameter)
        {
            _execute(parameter);
        }

        public void RaiseCanExecuteChanged()
        {
            CommandManager.InvalidateRequerySuggested();
        }
    }
}