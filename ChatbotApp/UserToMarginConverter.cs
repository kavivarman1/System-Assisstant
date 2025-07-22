using System;
using System.Globalization;
using System.Windows;
using System.Windows.Data;

namespace ChatbotApp
{
    public class UserToMarginConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            bool isFromUser = (bool)value;
            return isFromUser ? new Thickness(80, 0, 0, 16) : new Thickness(0, 0, 80, 16);
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
} 