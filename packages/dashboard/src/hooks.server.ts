import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
  // Proxy API requests to collector
  if (event.url.pathname.startsWith('/api/')) {
    const collectorUrl = process.env.COLLECTOR_URL || 'http://localhost:3000';
    const targetPath = event.url.pathname.replace('/api/', '/v1/');
    const targetUrl = `${collectorUrl}${targetPath}${event.url.search}`;
    
    const headers = new Headers(event.request.headers);
    headers.delete('host');
    
    const response = await fetch(targetUrl, {
      method: event.request.method,
      headers,
      body: event.request.method !== 'GET' ? await event.request.text() : undefined,
    });
    
    return new Response(response.body, {
      status: response.status,
      headers: response.headers,
    });
  }
  
  return resolve(event);
};
