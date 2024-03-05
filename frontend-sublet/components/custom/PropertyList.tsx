import Property from "./Property";
import { PropertyInterface } from "@/interfaces/Property";

interface PropertyListProps {
  properties: PropertyInterface[];
}

const PropertyList: React.FC<PropertyListProps> = ({ properties }) => {
  return (
    <ul className="grid lg:grid-cols-3 sm:grid-cols-2 gap-8 list-none">
      {properties.map((property) => (
        <li key={property.id}>
          <Property property={property} />
        </li>
      ))}
    </ul>
  );
};

export default PropertyList;
