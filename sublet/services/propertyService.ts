import { PropertyInterface } from '../interfaces/Property';

export const fetchProperties = async (): Promise<PropertyInterface[]> => {
  // Retrieve username and password from environment variables
  const username = process.env.NEXT_PUBLIC_API_USERNAME;
  const password = process.env.NEXT_PUBLIC_API_PASSWORD;
  const url = `${process.env.NEXT_PUBLIC_BASE_URL}/properties/`

  console.log(process.env.NEXT_PUBLIC_BASE_URL);

  if (!username || !password) {
    console.error('API credentials are not set in environment variables.');
    throw new Error('API credentials are missing.');
  }

  const encodedCredentials = btoa(`${username}:${password}`);

  // Set up the HTTP headers with Basic Authentication
  const headers = new Headers({
    'Authorization': `Basic ${encodedCredentials}`
  });

  // Make the fetch request with the headers
  const response = await fetch(url, {
    method: 'GET',
    headers: headers
  });

  // Check if the response was not ok
  if (!response.ok) {
    // Attempt to parse the error response body
    let errorMsg = `Error ${response.status}: ${response.statusText}`;
    try {
      const errorBody = await response.json();
      errorMsg += `: ${errorBody.detail || JSON.stringify(errorBody)}`;
    } catch (e) {
      // If there's an error parsing the error response, log it
      console.error('Error parsing the error response:', e);
    }

    // Throw a new error with the error message
    throw new Error(errorMsg);
  }

  const properties: PropertyInterface[] = await response.json();
  return properties;
};