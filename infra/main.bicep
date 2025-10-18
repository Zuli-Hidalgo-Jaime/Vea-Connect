targetScope = 'subscription'

@description('Nombre del proyecto')
param projectName string = 'vea'

@description('Ubicación de los recursos')
param location string = resourceGroup().location

@description('Tamaño de la VM para Redis')
param vmSize string = 'Standard_B2s'

@description('Contraseña del administrador de PostgreSQL')
@secure()
param postgresAdminPassword string

@description('Contraseña de Redis')
@secure()
param redisPassword string

@description('Django Secret Key')
@secure()
param djangoSecretKey string

@description('Nombre del usuario de la VM')
param vmAdminUsername string = 'azureuser'

// Variables
var resourceGroupName = resourceGroup().name
var appServicePlanName = '${projectName}-app-service-plan'
var appServiceName = '${projectName}-webapp-process-botconnect'
var functionAppName = '${projectName}-embedding-api'
var postgresServerName = '${projectName}-postgresql-server'
var postgresDbName = '${projectName}_database'
var storageAccountName = '${projectName}storage${uniqueString(resourceGroup().id)}'
var vmName = '${projectName}-redis-vm'
var keyVaultName = '${projectName}-key-vault'
var vnetName = '${projectName}-vnet'
var subnetName = '${projectName}-subnet'
var nsgName = '${projectName}-nsg'
var publicIpName = '${projectName}-public-ip'
var nicName = '${projectName}-nic'

// Tags comunes
var commonTags = {
  project: projectName
  environment: 'production'
  managedBy: 'bicep'
  costCenter: 'development'
}

// 1. Virtual Network
resource vnet 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: vnetName
  location: location
  tags: commonTags
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.0.0.0/16'
      ]
    }
    subnets: [
      {
        name: subnetName
        properties: {
          addressPrefix: '10.0.1.0/24'
          networkSecurityGroup: {
            id: nsg.id
          }
        }
      }
    ]
  }
}

// 2. Network Security Group
resource nsg 'Microsoft.Network/networkSecurityGroups@2023-09-01' = {
  name: nsgName
  location: location
  tags: commonTags
  properties: {
    securityRules: [
      {
        name: 'SSH'
        properties: {
          priority: 1000
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Inbound'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '22'
        }
      }
      {
        name: 'Redis'
        properties: {
          priority: 1001
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Inbound'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '6379'
        }
      }
      {
        name: 'RedisInsight'
        properties: {
          priority: 1002
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Inbound'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '8001'
        }
      }
      {
        name: 'HTTP'
        properties: {
          priority: 1003
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Inbound'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '80'
        }
      }
      {
        name: 'HTTPS'
        properties: {
          priority: 1004
          protocol: 'Tcp'
          access: 'Allow'
          direction: 'Inbound'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '443'
        }
      }
    ]
  }
}

// 3. Public IP para VM
resource publicIp 'Microsoft.Network/publicIPAddresses@2023-09-01' = {
  name: publicIpName
  location: location
  tags: commonTags
  properties: {
    publicIPAllocationMethod: 'Static'
    dnsSettings: {
      domainNameLabel: '${projectName}-redis-vm'
    }
  }
}

// 4. Network Interface para VM
resource nic 'Microsoft.Network/networkInterfaces@2023-09-01' = {
  name: nicName
  location: location
  tags: commonTags
  properties: {
    ipConfigurations: [
      {
        name: 'ipconfig1'
        properties: {
          privateIPAllocationMethod: 'Dynamic'
          publicIPAddress: {
            id: publicIp.id
          }
          subnet: {
            id: vnet.properties.subnets[0].id
          }
        }
      }
    ]
  }
}

// 5. Virtual Machine para Redis Stack
resource vm 'Microsoft.Compute/virtualMachines@2023-09-01' = {
  name: vmName
  location: location
  tags: commonTags
  properties: {
    hardwareProfile: {
      vmSize: vmSize
    }
    osProfile: {
      computerName: vmName
      adminUsername: vmAdminUsername
      adminPassword: redisPassword
    }
    storageProfile: {
      imageReference: {
        publisher: 'Canonical'
        offer: '0001-com-ubuntu-server-focal'
        sku: '20_04-lts'
        version: 'latest'
      }
      osDisk: {
        name: '${vmName}-osdisk'
        caching: 'ReadWrite'
        createOption: 'FromImage'
        managedDisk: {
          storageAccountType: 'Standard_LRS'
        }
        diskSizeGB: 30
      }
    }
    networkProfile: {
      networkInterfaces: [
        {
          id: nic.id
        }
      ]
    }
  }
}

// 6. App Service Plan
resource appServicePlan 'Microsoft.Web/serverfarms@2023-06-01' = {
  name: appServicePlanName
  location: location
  tags: commonTags
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

// 7. App Service
resource appService 'Microsoft.Web/sites@2023-06-01' = {
  name: appServiceName
  location: location
  tags: commonTags
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.10'
      appSettings: [
        {
          name: 'AZURE_POSTGRESQL_NAME'
          value: postgresDbName
        }
        {
          name: 'AZURE_POSTGRESQL_USERNAME'
          value: 'vea_admin@${postgresServerName}'
        }
        {
          name: 'AZURE_POSTGRESQL_PASSWORD'
          value: postgresAdminPassword
        }
        {
          name: 'AZURE_POSTGRESQL_HOST'
          value: '${postgresServerName}.postgres.database.azure.com'
        }
        {
          name: 'DB_PORT'
          value: '5432'
        }
        {
          name: 'AZURE_STORAGE_CONNECTION_STRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
        {
          name: 'BLOB_ACCOUNT_NAME'
          value: storageAccountName
        }
        {
          name: 'BLOB_ACCOUNT_KEY'
          value: storageAccount.listKeys().keys[0].value
        }
        {
          name: 'BLOB_CONTAINER_NAME'
          value: 'documents'
        }
        {
          name: 'REDIS_HOST'
          value: publicIp.properties.ipAddress
        }
        {
          name: 'REDIS_PORT'
          value: '6379'
        }
        {
          name: 'REDIS_PASSWORD'
          value: redisPassword
        }
        {
          name: 'REDIS_DB'
          value: '0'
        }
        {
          name: 'DEBUG'
          value: 'False'
        }
        {
          name: 'SECRET_KEY'
          value: djangoSecretKey
        }
        {
          name: 'ALLOWED_HOSTS'
          value: '${appServiceName}.azurewebsites.net,localhost,127.0.0.1'
        }
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '0'
        }
      ]
    }
  }
}

// 8. PostgreSQL Flexible Server
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: postgresServerName
  location: location
  tags: commonTags
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    administratorLogin: 'vea_admin'
    administratorLoginPassword: postgresAdminPassword
    version: '13'
    storage: {
      storageSizeGB: 32
    }
    network: {
      delegatedSubnetResourceId: vnet.properties.subnets[0].id
      privateDnsZoneArmResourceId: ''
    }
  }
}

// 9. PostgreSQL Database
resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: postgresServer
  name: postgresDbName
  properties: {
    charset: 'utf8'
    collation: 'utf8_general_ci'
  }
}

// 10. Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: commonTags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// 11. Storage Containers
resource staticContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: storageAccount::'default'
  name: 'static'
  properties: {
    publicAccess: 'None'
  }
}

resource mediaContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: storageAccount::'default'
  name: 'media'
  properties: {
    publicAccess: 'None'
  }
}

resource documentsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: storageAccount::'default'
  name: 'documents'
  properties: {
    publicAccess: 'None'
  }
}

// 12. Key Vault (opcional pero recomendado)
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: commonTags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// 13. Azure Function App
resource functionApp 'Microsoft.Web/sites@2023-06-01' = {
  name: functionAppName
  location: location
  tags: commonTags
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      appSettings: [
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
        {
          name: 'AZURE_POSTGRESQL_NAME'
          value: postgresDbName
        }
        {
          name: 'AZURE_POSTGRESQL_USERNAME'
          value: 'vea_admin@${postgresServerName}'
        }
        {
          name: 'AZURE_POSTGRESQL_PASSWORD'
          value: postgresAdminPassword
        }
        {
          name: 'AZURE_POSTGRESQL_HOST'
          value: '${postgresServerName}.postgres.database.azure.com'
        }
        {
          name: 'REDIS_HOST'
          value: publicIp.properties.ipAddress
        }
        {
          name: 'REDIS_PORT'
          value: '6379'
        }
        {
          name: 'REDIS_PASSWORD'
          value: redisPassword
        }
        {
          name: 'AZURE_STORAGE_CONNECTION_STRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: 'https://your-openai-resource.openai.azure.com/'
        }
        {
          name: 'AZURE_OPENAI_API_KEY'
          value: 'your-openai-api-key'
        }
      ]
    }
  }
}

// Outputs
output appServiceUrl string = 'https://${appService.properties.defaultHostName}'
output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output postgresServerFqdn string = postgresServer.properties.fullyQualifiedDomainName
output storageAccountName string = storageAccount.name
output vmPublicIp string = publicIp.properties.ipAddress
output redisInsightUrl string = 'http://${publicIp.properties.ipAddress}:8001'
output keyVaultName string = keyVault.name

output connectionStrings object = {
  postgres: 'Server=${postgresServer.properties.fullyQualifiedDomainName};Database=${postgresDbName};Port=5432;User Id=vea_admin@${postgresServerName};Password=${postgresAdminPassword};Ssl Mode=Require;'
  redis: 'redis://:${redisPassword}@${publicIp.properties.ipAddress}:6379/0'
  storage: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
}
