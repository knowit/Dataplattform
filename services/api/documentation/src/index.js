import SwaggerUI from 'swagger-ui'
import 'swagger-ui/dist/swagger-ui.css';


const ui = SwaggerUI({
    url: `https://${API_URL}/schema.json`,
    dom_id: '#swagger',
});

ui.initOAuth({
    appName: 'Dataplattform API Demo',
    clientId: DEMO_CLIENT_ID,
    scopes: 'openid',
    useBasicAuthenticationWithAccessCodeGrant: true,
    usePkceWithAuthorizationCodeGrant: true
});