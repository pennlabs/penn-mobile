import { PropertyInterface } from '../interfaces/Property';
import apiRequest from './fetch';

export const fetchProperties = async (): Promise<PropertyInterface[]> => {
  const properties: PropertyInterface[] = await apiRequest("properties", "GET");
  return properties;
};

export const createProperty = async (property: any): Promise<any> => {
  const newProperty: PropertyInterface = await apiRequest("properties", "POST", property);
  return newProperty
};

export const createPropertyImage = async (sublet_id: string, image: File): Promise<any> => {
  // Create FormData object to hold the image data
  const formData = new FormData();
  formData.append('sublet', sublet_id); // The 'sublet' field must be an integer
  formData.append('images', image); // 'image' should be the File object

  return await apiRequest(`properties/${sublet_id}/images`, 'POST', formData)
};

export const fetchAmenities = async (): Promise<string[]> => {
  const amenities: string[] = await apiRequest("amenities", "GET");
  return amenities;
};