using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows.Input;
using System.Threading.Tasks;

namespace ChatbotApp
{
    public class MainWindowViewModel : INotifyPropertyChanged, IDisposable
    {
        private string _currentMessage = string.Empty;
        private bool _isTyping;
        private bool _isDarkTheme;
        private PythonChatbotBridge chatbotBridge;
        public event PropertyChangedEventHandler? PropertyChanged = delegate { };

        public MainWindowViewModel()
        {
            Messages = new ObservableCollection<ChatMessage>();
            SendCommand = new RelayCommand(SendMessage, CanSendMessage);
            VoiceCommand = new RelayCommand(StartVoiceInput);
            AttachCommand = new RelayCommand(AttachFile);
            SettingsCommand = new RelayCommand(OpenSettings);
            ThemeToggleCommand = new RelayCommand(ToggleTheme);
            
            IsDarkTheme = true;
            chatbotBridge = new PythonChatbotBridge();
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

        private bool CanSendMessage(object parameter)
        {
            return !string.IsNullOrWhiteSpace(CurrentMessage) && !IsTyping;
        }

        public async void SendMessage(object parameter)
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

            IsTyping = true;
            try
            {
                string aiResponse = await chatbotBridge.SendMessageAsync(userMessage);
                Messages.Add(new ChatMessage
                {
                    Content = aiResponse,
                    IsFromUser = false,
                    Timestamp = DateTime.Now
                });
            }
            catch (Exception ex)
            {
                Messages.Add(new ChatMessage
                {
                    Content = $"[Error communicating with Gemini: {ex.Message}]",
                    IsFromUser = false,
                    Timestamp = DateTime.Now
                });
            }
            IsTyping = false;
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

        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        public void Dispose()
        {
            chatbotBridge?.Dispose();
        }
    }

    public class ChatMessage : INotifyPropertyChanged
    {
        private string _content = string.Empty;
        private bool _isFromUser;
        private DateTime _timestamp;
        public event PropertyChangedEventHandler? PropertyChanged = delegate { };

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