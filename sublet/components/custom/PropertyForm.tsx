"use client"

import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"

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

import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label";
import { CalendarIcon, CrossCircledIcon } from "@radix-ui/react-icons";
import { Popover, PopoverContent, PopoverTrigger } from "../ui/popover";
import { Calendar } from "../ui/calendar";
import { cn } from "@/lib/utils";
import { format } from "date-fns";

const uriRegex = new RegExp('^(?:[a-z0-9.+-]*)://(?:[^\s:@/]+(?::[^\s:@/]*)?@)?(?:(?:0|25[0-5]|2[0-4][0-9]|1[0-9]?[0-9]?|[1-9][0-9]?)(?:\.(?:0|25[0-5]|2[0-4][0-9]|1[0-9]?[0-9]?|[1-9][0-9]?)){3}|\[[0-9a-f:.]+\]|([a-z¡-￿0-9](?:[a-z¡-￿0-9-]{0,61}[a-z¡-￿0-9])?(?:\.(?!-)[a-z¡-￿0-9-]{1,63}(?<!-))*\.(?!-)(?:[a-z¡-￿-]{2,63}|xn--[a-z0-9]{1,59})(?<!-)\.?|localhost))(?::[0-9]{1,5})?(?:[/?#][^\s]*)?\z');

const decimalRegex = /^-?\d+(\.\d)?$/;

const formSchema = z.object({
  amenities: z.array(z.string().max(255)),
  title: z.string().max(255),
  address: z.string().max(255).optional(),
  beds: z.number().min(-2147483648).max(2147483647).nullable(),
  baths: z.union([
    z.string().regex(decimalRegex).nullable().transform((val) => val !== null ? parseFloat(val) : null),
    z.number().min(-100).max(100).nullable()
  ]).refine((val) => val === null || (typeof val === 'number' && val >= -100 && val <= 100 && decimalRegex.test(val.toString())), {
    message: "Baths must be a decimal with at most one decimal place and within the range -100 to 100."
  }),
  description: z.string().nullable(),
  external_link: z.string().regex(uriRegex).max(255),
  price: z.preprocess((value) => {
    // If value is already a number, return it
    if (typeof value === 'number') return value;
    // If it's a string, attempt to parse it
    if (typeof value === 'string') return parseFloat(value);
  }, z.number().min(-2147483648).max(2147483647)),
  negotiable: z.boolean().optional(),
  start_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  end_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  expires_at: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/),
});

interface PropertyFormProps {
  children: React.ReactNode;
}

const PropertyForm = ({ children }: PropertyFormProps) => {

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      amenities: [],
      title: "",
      address: "123",
      beds: null,
      baths: null,
      description: "",
      external_link: "",
      price: 0,
      negotiable: false,
      start_date: "",
      end_date: "",
      expires_at: "",
    },
  })

  function onSubmit(values: z.infer<typeof formSchema>) {
    // Do something with the form values.
    // ✅ This will be type-safe and validated.
    console.log(values)
  }

  return (
    <div>
      <Sheet>
        <SheetTrigger asChild>
          {children}
        </SheetTrigger>
        <SheetContent className="space-y-4">
          <SheetHeader>
            <SheetTitle className="text-2xl">New Listing</SheetTitle>
            <SheetDescription>
              Create a new property listing below. Make sure to fill in all required fields.
            </SheetDescription>
          </SheetHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-4">
                    <FormLabel htmlFor="title" className="text-right">Name</FormLabel>
                    <FormControl className="col-span-3">
                      <Input placeholder="Chestnut 2bed 2ba" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="price"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-4">
                    <FormLabel htmlFor="price" className="text-right">Price</FormLabel>
                    <FormControl className="col-span-3">
                      <Input type="number" placeholder="1000" {...field} />
                    </FormControl>
                    <FormMessage className="col-span-4" />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="negotiable"
                render={({ field }) => (
                  <FormItem className="flex justify-end items-center gap-4">
                    <div className="flex gap-2">
                      <FormControl className="">
                        <Checkbox
                          onClick={(e) => {
                            //const checked = (e.target as HTMLInputElement).checked;
                            //field.onChange(checked); // Use the form library's onChange method
                            field.value = !field.value;
                            console.log(field.value);
                          }}
                        />
                      </FormControl>
                      <FormLabel htmlFor="negotiable" className="text-right col-start-3">
                        Negotiable?
                      </FormLabel>
                    </div>
                    <FormMessage className="col-span-4" />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="address"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-4">
                    <FormLabel htmlFor="address" className="text-right">Address</FormLabel>
                    <FormControl className="col-span-3">
                      <Input type="string" placeholder="123 Main St, New York, NY 10001" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="start_date"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-4">
                    <FormLabel htmlFor="start_date" className="text-right">Start Date</FormLabel>
                    <Popover>
                      <PopoverTrigger asChild>
                        <FormControl className="col-span-3">
                          <Button
                            variant={"outline"}
                            className={cn(
                              "w-[240px] pl-3 text-left font-normal",
                              !field.value && "text-muted-foreground"
                            )}
                          >
                            {field.value ? (
                              format(field.value, "PPP")
                            ) : (
                              <span>Pick a date</span>
                            )}
                            <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                          </Button>
                        </FormControl>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          selected={new Date(field.value)}
                          onSelect={field.onChange}
                          disabled={(date) =>
                            date > new Date() || date < new Date("1900-01-01")
                          }
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <SheetFooter className="max-sm:flex max-sm: max-sm:gap-2">
                <SheetClose asChild>
                  <Button variant="secondary" type="submit">Close</Button>
                </SheetClose>
                <Button type="submit">Save</Button>
              </SheetFooter>

            </form>
          </Form>
          {/*
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-4 items-center gap-4">
                  <FormLabel htmlFor="title" className="text-right">
                    Title
                  </FormLabel>
                  <Input
                    id="title"
                    placeholder="Spacious 2 Bedroom Apartment"
                    className="col-span-3"
                    {...form.register("title")}
                  />
                  <FormMessage>{form.formState.errors.title?.message}</FormMessage>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <FormLabel htmlFor="address" className="text-right">
                    Address
                  </FormLabel>
                  <Input
                    id="address"
                    placeholder="123 Main St, New York, NY 10001"
                    className="col-span-3"
                    {...form.register("address")}
                  />
                  <FormMessage>{form.formState.errors.address?.message}</FormMessage>
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <FormLabel htmlFor="price" className="text-right">
                    Price
                  </FormLabel>
                  <Input
                    id="price"
                    placeholder="1000"
                    className="col-span-3"
                    type="number"
                    {...form.register("price")}
                  />
                  <FormMessage className="col-span-4 flex gap-1 items-center justify-center">
                    {form.formState.errors.price ? <CrossCircledIcon /> : <></>}
                    {form.formState.errors.price?.message}
                  </FormMessage>
                </div>
              </div>
              <SheetFooter>
                <SheetClose asChild>
                  <Button type="submit">Submit</Button>
                </SheetClose>
              </SheetFooter>
            </form>
          </Form>
          
          
          
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="name" className="text-right">
                Name
              </Label>
              <Input
                id="name"
                placeholder="Pedro Duarte"
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
                </SheetFooter>*/}
        </SheetContent>
      </Sheet >
    </div >
  )
}

export default PropertyForm