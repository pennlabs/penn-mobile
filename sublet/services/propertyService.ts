import { PropertyInterface } from '../interfaces/Property';
import getCsrfTokenCookie from '../utils/csrf';

export const fetchProperties = async (): Promise<PropertyInterface[]> => {
  // Retrieve username and password from environment variables
  const username = process.env.NEXT_PUBLIC_API_USERNAME;
  const password = process.env.NEXT_PUBLIC_API_PASSWORD;
  const url = `${process.env.NEXT_PUBLIC_BASE_URL}/properties/`

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

export const createProperty = async (property: any): Promise<any> => {
  // Retrieve username and password from environment variables
  const username = process.env.NEXT_PUBLIC_API_USERNAME;
  const password = process.env.NEXT_PUBLIC_API_PASSWORD;
  const url = `${process.env.NEXT_PUBLIC_BASE_URL}/properties/`

  if (!username || !password) {
    console.error('API credentials are not set in environment variables.');
    throw new Error('API credentials are missing.');
  }

  const encodedCredentials = btoa(`${username}:${password}`);

  const csrfToken = getCsrfTokenCookie();

  // Set up the HTTP headers with Basic Authentication
  const headers = new Headers({
    'Authorization': `Basic ${encodedCredentials}`,
    'Content-Type': 'application/json',
    'X-CSRFToken': csrfToken
  });

  // Make the fetch request with the headers
  const response = await fetch(url, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(property),
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
  } else {
    return await response.json();
  }
};

export const createPropertyImage = async (sublet_id: string, image: File): Promise<any> => {
  // Retrieve username and password from environment variables
  const username = process.env.NEXT_PUBLIC_API_USERNAME;
  const password = process.env.NEXT_PUBLIC_API_PASSWORD;
  const url = `${process.env.NEXT_PUBLIC_BASE_URL}/properties/${sublet_id}/images/`

  if (!username || !password) {
    console.error('API credentials are not set in environment variables.');
    throw new Error('API credentials are missing.');
  }

  const encodedCredentials = btoa(`${username}:${password}`);

  const csrfToken = getCsrfTokenCookie();

  // Create FormData object to hold the image data
  const formData = new FormData();
  formData.append('sublet', sublet_id); // The 'sublet' field must be an integer
  formData.append('images', image); // 'image' should be the File object

  // Set up the HTTP headers with Basic Authentication
  const headers = new Headers({
    'Authorization': `Basic ${encodedCredentials}`,
    // 'Content-Type': 'multipart/form-data' is not needed, as it will be set automatically with the correct boundary by the FormData
    'X-CSRFToken': csrfToken
  });

  Array.from(formData.entries()).forEach(([key, value]) => {
    console.log(`${key}: ${value}`);
  });

  console.log("-");

  // Make the fetch request with the headers
  const response = await fetch(url, {
    method: 'POST',
    headers: headers,
    body: formData, // use FormData object here instead of JSON
  });

  if (!response.ok) {
    console.error(`HTTP error ${response.status}: ${response.statusText}`);
    throw new Error(`HTTP error ${response.status}`);
  } else {
    return await response.json();
  }
};

export const fetchAmenities = async (): Promise<string[]> => {
  // Retrieve username and password from environment variables
  const username = process.env.NEXT_PUBLIC_API_USERNAME;
  const password = process.env.NEXT_PUBLIC_API_PASSWORD;
  const url = `${process.env.NEXT_PUBLIC_BASE_URL}/amenities/`

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

  const amenities: string[] = await response.json();
  return amenities;
};