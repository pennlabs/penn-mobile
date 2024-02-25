



const BASE_URL = 'https://pennmobile.org/sublet';

// Function to fetch properties
export async function fetchProperties() {
  try {
    const response = await fetch(`${BASE_URL}/properties/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Include authorization header if required
        'Authorization': 'Bearer YOUR_TOKEN_HERE',
      },
    });
    if (response.ok) {
      const data = await response.json();
      return data;
    }
    throw new Error('Failed to fetch properties');
  } catch (error) {
    console.error("Error fetching properties:", error);
    throw error;
  }
}

interface propertyData {
  title: string;
  description: string;
  price: number;
  location: string;
  imageUrl: string;
}

// Function to create a property
export async function createProperty(propertyData: any) {
  try {
    const response = await fetch(`${BASE_URL}/properties/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_TOKEN_HERE', // Include if needed
      },
      body: JSON.stringify(propertyData),
    });
    if (response.ok) {
      return await response.json();
    }
    throw new Error('Failed to create property');
  } catch (error) {
    console.error("Error creating property:", error);
    throw error;
  }
}
