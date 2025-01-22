from datetime import datetime
import pytz
import locale
import geocoder
from dataclasses import dataclass
from config.log import logger

@dataclass
class UserSettings:
    country: str
    timezone: str
    locale: str
    current_time: datetime
    currency: str
    
    @classmethod
    def auto_detect(cls) -> 'UserSettings':
        """Automatically detect user settings dynamically."""
        try:
            # Detect country using geolocation
            location = geocoder.ip('me')
            country = location.country if location and location.country else "Unknown"
            
            # Detect timezone using geolocation
            if location and location.latlng:
                country_timezones = pytz.country_timezones.get(location.country, [])
                local_tz = pytz.timezone(country_timezones[0]) if country_timezones else pytz.UTC
            else:
                local_tz = pytz.UTC
            
            # Get current time in detected timezone
            current_time = datetime.now(local_tz)
            
            # Detect locale based on country
            if country != "Unknown":
                locale_str = f'en_{country.upper()}.UTF-8'
            else:
                locale_str = 'en_US.UTF-8'
            locale.setlocale(locale.LC_ALL, locale_str)
            
            # Set currency based on country
            country_currency_map = {
                'US': 'USD',
                'CA': 'CAD',
                'GB': 'GBP',
                'AU': 'AUD',
                'IN': 'INR',
                # Add more mappings as needed
            }
            currency = country_currency_map.get(country, 'USD')  # Default to USD
            
            logger.info(f"Detected user settings: Country={country}, Timezone={local_tz}, Current time={current_time}")
            
            return cls(
                country=country,
                timezone=str(local_tz),
                locale=locale_str,
                current_time=current_time,
                currency=currency
            )
        except Exception as e:
            logger.error(f"Error detecting user settings: {str(e)}")
            return cls(
                country="Unknown",
                timezone="UTC",
                locale="en_US.UTF-8",
                current_time=datetime.now(pytz.UTC),
                currency="USD"
            )