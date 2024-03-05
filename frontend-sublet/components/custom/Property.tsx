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
import Image from "next/image";
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

import { PropertyInterface, ImageInterface } from "@/interfaces/Property";

interface PropertyProps {
  property: PropertyInterface;
}

const Property: React.FC<PropertyProps> = ({ property }) => {
  return (
    <div>
      <Card className="w-[380px] mb-[20px]">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>{property.title}</CardTitle>
            <DropdownMenu>
              <DropdownMenuTrigger>
                <Dots className="w-4 h-4" />
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem className="text-red-500 focus:text-red-500">
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="flex items-center space-x-4 rounded-md">
            <Image
              className="rounded-lg select-none"
              draggable="false"
              src={"/hamco.jpeg"}
              alt="Property image"
              width={400}
              height={400}
            />
          </div>

          <div className="mb-4 items-start pb-4 pt-2 space-y-1 last:mb-0 last:pb-0">
            <div className="flex items-center gap-2">
              <div className="relative">
                <span className="flex h-3 w-3 rounded-full bg-green-500" />
                <span className="flex h-3 w-3 rounded-full bg-green-500 animate-ping absolute top-0" />
              </div>
              <p className="text-sm font-medium leading-none">Pending</p>
            </div>
            <p className="text-sm text-muted-foreground">Jun 27 - Jul 24</p>
          </div>
        </CardContent>
        <CardFooter>
          <div className="flex justify-between gap-3">
            <Button className="w-full gap-4">
              <CheckIcon className="ml-[-4px] mr-[-10px]" />
              Mark as Claimed
            </Button>

            <Sheet>
              <SheetTrigger asChild>
                <Button variant="secondary" className="w-full">
                  Edit
                </Button>
              </SheetTrigger>
              <SheetContent>
                <SheetHeader>
                  <SheetTitle>Edit profile</SheetTitle>
                  <SheetDescription>
                    Make changes to your profile here. Click save when you're
                    done.
                  </SheetDescription>
                </SheetHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="name" className="text-right">
                      Name
                    </Label>
                    <Input
                      id="name"
                      value="Pedro Duarte"
                      className="col-span-3"
                    />
                  </div>
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="username" className="text-right">
                      Username
                    </Label>
                    <Input
                      id="username"
                      value="@peduarte"
                      className="col-span-3"
                    />
                  </div>
                </div>
                <SheetFooter>
                  <SheetClose asChild>
                    <Button type="submit">Save changes</Button>
                  </SheetClose>
                </SheetFooter>
              </SheetContent>
            </Sheet>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
};

export default Property;
