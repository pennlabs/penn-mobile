{/*
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { CheckIcon, DotsHorizontalIcon as Dots } from "@radix-ui/react-icons";
*/}

import { Card, CardContent } from "@/components/ui/card"
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";

import Image from "next/image";

import { PropertyInterface, ImageInterface } from "@/interfaces/Property";

function formatDate(dateString: string): string {
  // Convert the input string to a Date object
  const date = new Date(dateString);

  // Format the date to the desired format
  const formattedDate = date.toLocaleDateString('en-US', {
    month: 'short', // Abbreviated month name
    day: 'numeric'  // Numeric day of the month
  });

  return formattedDate;
}

interface PropertyProps {
  property: PropertyInterface;
}

const Property: React.FC<PropertyProps> = ({ property }) => {
  return (
    <div className="space-y-1">
      <Carousel className="w-full max-w-xs rounded-xl overflow-hidden">
        <CarouselContent className="">
          {Array.from({ length: 5 }).map((_, index) => (
            <CarouselItem key={index}>
              <div className="flex items-center justify-center">
                <Image
                  className="rounded-xl select-none"
                  draggable="false"
                  src={"/hamco.jpeg"}
                  alt="Property image"
                  width={800}
                  height={800}
                />
              </div>
            </CarouselItem>
          ))}
        </CarouselContent>
        <CarouselPrevious />
        <CarouselNext />
      </Carousel>

      <div className="flex justify-between pt-3">
        <div className="font-bold text-xl">{property.title}</div>
        <p className="text-xs font-medium text-muted-foreground">{formatDate(property.start_date)} - {formatDate(property.end_date)}</p>
        {/*<DropdownMenu>
          <DropdownMenuTrigger>
            <Dots className="w-4 h-4" />
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem className="text-red-500 focus:text-red-500">
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
  </DropdownMenu>*/}
      </div>

      <div className="mb-4 items-start pb-4 pt-2 space-y-1 last:mb-0 last:pb-0">
        <div className="flex items-center gap-2">
          <div className="relative">
            <span className="flex h-3 w-3 rounded-full bg-green-500" />
            <span className="flex h-3 w-3 rounded-full bg-green-500 animate-ping absolute top-0" />
          </div>
          <p className="text-sm font-medium leading-none">Pending</p>
        </div>

      </div>
      {/*<div className="flex justify-between gap-3">
        <Button className="w-full gap-4">
          <CheckIcon className="ml-[-4px] mr-[-10px]" />
          Mark as Claimed
        </Button>

        <PropertyForm>
          <Button variant="secondary" className="w-full">
            Edit
          </Button>
        </PropertyForm>
</div>*/}
    </div>
  );
};

export default Property;
