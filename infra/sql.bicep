@description('Nombre del servidor SQL')
param sqlServerName string = 'sql-${uniqueString(resourceGroup().id)}'

@description('Ubicación del servidor SQL')
param location string

@description('Etiquetas comunes')
param tags object = {}

@description('Usuario administrador del servidor SQL')
param administratorLogin string = 'sqladmin'

@secure()
@description('Contraseña del usuario administrador')
param administratorLoginPassword string

resource sqlServer 'Microsoft.Sql/servers@2022-11-01' = {
  name: sqlServerName
  location: location
  tags: tags
  properties: {
    administratorLogin: administratorLogin
    administratorLoginPassword: administratorLoginPassword
    version: '12.0'
    publicNetworkAccess: 'Enabled'
    minimalTlsVersion: '1.2'
  }
}

output serverName string = sqlServer.name
