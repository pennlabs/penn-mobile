import Property from "./Property";
import { PropertyInterface } from "@/interfaces/Property";

interface PropertyListProps {
  properties: PropertyInterface[];
}

const PropertyList: React.FC<PropertyListProps> = ({ properties }) => {
  return (
    <ul className="grid xl:grid-cols-3 xl:max-w-[76rem] lg:grid-cols-2 sm:grid-cols-1 gap-5 list-none">
      {properties.map((property) => (
        <li key={property.id}>
          <Property property={property} />
        </li>
      ))}
    </ul>
  );
};

export default PropertyList;
