import Property from "./Property";
import { PropertyInterface } from "@/interfaces/Property";

interface PropertyListProps {
  properties: PropertyInterface[];
}

const PropertyList: React.FC<PropertyListProps> = ({ properties }) => {
  return (
    <div className="grid xl:grid-cols-3 xl:max-w-[76rem] lg:grid-cols-2 sm:grid-cols-1 gap-5">
      {properties.map((property) => (
        <li key={property.id}>
          <div>Hi</div>
          <Property property={property} />
        </li>
      ))}
    </div>
  );
};

export default PropertyList;
