using System;
using System.Globalization;
using System.Windows.Data;
using System.Windows.Media;

namespace ChatbotApp
{
    public class UserToBackgroundConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            bool isFromUser = (bool)value;
            return isFromUser ?
                (Brush)App.Current.Resources["UserMessageBackgroundBrush"] :
                (Brush)App.Current.Resources["AiMessageBackgroundBrush"];
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
} 