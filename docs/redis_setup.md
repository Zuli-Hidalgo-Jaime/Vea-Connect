# Redis Client Setup for Azure Container Apps

This document describes the implementation of a secure Redis client for connecting to the `redis-stack-vea` instance deployed in Azure Container Apps.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   Django App    │───▶│   Redis Client       │───▶│  Azure Container    │
│                 │    │   (utilities/)       │    │  Apps Redis Stack   │
└─────────────────┘    └──────────────────────┘    └─────────────────────┘
```

## 📁 Files Structure

```
utilities/
├── redis_client.py      # Main Redis client implementation
├── redis_example.py     # Usage examples
└── ...

scripts/
└── test_redis_connection.py  # Connection testing script

config/settings/
└── base.py             # Redis configuration variables

env.example             # Environment variables template
```

## 🔧 Configuration

### Environment Variables

Add these variables to your `.env` file:

```env
# Redis Configuration for Azure Container Apps
AZURE_REDIS_CONNECTIONSTRING=your-redis-stack-vea.azurecontainerapps.io:6379
AZURE_REDIS_CONNECTIONSTRING=your-redis-password  # Optional - set to None if no password
```

### Settings Configuration

The Redis configuration is automatically loaded in `config/settings/base.py`:

```python
# Redis Configuration for Azure Container Apps
AZURE_REDIS_CONNECTIONSTRING = os.environ.get('AZURE_REDIS_CONNECTIONSTRING')
AZURE_REDIS_CONNECTIONSTRING = os.environ.get('AZURE_REDIS_CONNECTIONSTRING')
```

## 🚀 Usage

### Basic Usage

```python
from utilities.redis_client import get_redis_client

# Get Redis client instance
client = get_redis_client()

# Basic operations
client.set("key", "value", ex=3600)  # Set with expiration
value = client.get("key")            # Get value
exists = client.exists("key")        # Check if key exists
client.delete("key")                 # Delete key
```

### Connection Testing

Run the connection test script:

```bash
python scripts/test_redis_connection.py
```

### Examples

Run the usage examples:

```bash
python utilities/redis_example.py
```

## 🔒 Security Features

### SSL/TLS Encryption
- SSL disabled by default for Azure Container Apps Redis
- Can be enabled if SSL is configured in the container
- Connection security through Azure Container Apps networking

### Connection Security
- Password authentication optional (can be None)
- Connection timeout: 10 seconds
- Operation timeout: 30 seconds
- Health check interval: 30 seconds

### Error Handling
- Comprehensive exception handling
- Connection validation with ping
- Graceful fallback on connection failures

## 📊 Features

### Core Operations
- ✅ SET/GET operations
- ✅ DELETE operations
- ✅ EXISTS checks
- ✅ TTL management
- ✅ EXPIRE operations

### Advanced Features
- ✅ Connection pooling (20 connections)
- ✅ Automatic reconnection
- ✅ Health monitoring
- ✅ Singleton pattern
- ✅ Thread-safe operations

### Data Structures Support
- ✅ Strings (basic operations)
- ✅ Lists (via underlying client)
- ✅ Sets (via underlying client)
- ✅ Hashes (via underlying client)

## 🧪 Testing

### Connection Test
```python
from utilities.redis_client import test_redis_connection

result = test_redis_connection()
print(f"Connected: {result['connected']}")
print(f"Message: {result['message']}")
```

### Manual Testing
```python
from utilities.redis_client import get_redis_client

client = get_redis_client()

# Test basic operations
client.set("test_key", "test_value", ex=60)
value = client.get("test_key")
print(f"Retrieved: {value}")

# Cleanup
client.delete("test_key")
```

## 🔧 Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check `AZURE_REDIS_CONNECTIONSTRING` format (host:port)
   - Verify `AZURE_REDIS_CONNECTIONSTRING` is correct
   - Ensure network connectivity to Azure Container Apps

2. **SSL Certificate Errors**
   - SSL certificate verification is disabled by default
   - If issues persist, check Azure Container Apps SSL configuration

3. **Timeout Errors**
   - Increase timeout values in Redis client configuration
   - Check network latency to Azure Container Apps

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('utilities.redis_client').setLevel(logging.DEBUG)
```

## 📈 Performance

### Connection Pooling
- Maximum 20 connections
- Automatic connection management
- Health check every 30 seconds

### Caching Strategy
- TTL-based expiration
- Automatic cleanup
- Memory-efficient operations

### Monitoring
- Connection status monitoring
- Operation success/failure tracking
- Performance metrics logging

## 🔄 Integration with Django

### Cache Backend
The Redis client can be used as a Django cache backend:

```python
# settings.py
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://:{AZURE_REDIS_CONNECTIONSTRING}@{AZURE_REDIS_CONNECTIONSTRING}/0",
    }
}
```

### Session Storage
Configure Redis for session storage:

```python
# settings.py
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
```

## 🚀 Deployment

### Production Configuration
1. Set environment variables in Azure App Service
2. Configure Azure Key Vault for secrets
3. Enable SSL/TLS encryption
4. Monitor connection health

### Azure Container Apps
1. Deploy Redis Stack to Azure Container Apps
2. Configure networking and security
3. Set up monitoring and alerting
4. Test connection from Django app

## 📚 API Reference

### RedisClient Class

#### Methods
- `get(key: str) -> Optional[str]`
- `set(key: str, value: str, ex: Optional[int] = None) -> bool`
- `delete(key: str) -> int`
- `exists(key: str) -> bool`
- `expire(key: str, time: int) -> bool`
- `ttl(key: str) -> int`
- `is_connected() -> bool`

#### Properties
- `client` - Access to underlying Redis client

### Utility Functions
- `get_redis_client() -> RedisClient`
- `test_redis_connection() -> Dict[str, Any]`

## 🔗 Related Documentation

- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Redis-py Documentation](https://redis-py.readthedocs.io/)
- [Django Redis Documentation](https://django-redis.readthedocs.io/)

## 📞 Support

For issues related to:
- **Redis Client**: Check the troubleshooting section
- **Azure Container Apps**: Refer to Azure documentation
- **Django Integration**: Check Django Redis documentation 