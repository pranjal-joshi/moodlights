import sys
sys.path.insert(0, '.')
try:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    print('HomeAssistant imports successful')
    
    # Test the integration
    try:
        import moodlights
        print('moodlights module imported successfully')
        
        # Test async_setup
        try:
            from moodlights import async_setup
            print('async_setup found')
            print('Running async_setup...')
            async_setup(None, {})
            print('async_setup completed')
        except Exception as e:
            print('async_setup error:', e)
            
        # Test async_setup_entry
        try:
            from moodlights import async_setup_entry
            print('async_setup_entry found')
            print('Creating mock entry...')
            mock_entry = ConfigEntry(
                entry_id='test123',
                domain='moodlights',
                title='Test mood',
                data={'moods': [{}]},
                source='user',
                version=1
            )
            print('Mock entry created')
            async_setup_entry(None, mock_entry)
            print('async_setup_entry completed')
        except Exception as e:
            print('async_setup_entry error:', e)
            
    except ImportError as e:
        print('Import error:', e)
        
except Exception as e:
    print('HomeAssistant import error:', e)
    import traceback
    traceback.print_exc()
