"use client"

import { fetchAmenities, createProperty } from "@/services/propertyService"

import { z } from "zod"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
//import { useToast } from "@/components/ui/use-toast"

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
import { Textarea } from "../ui/textarea";
import { useEffect, useState } from "react"
import { ToggleGroup, ToggleGroupItem } from "../ui/toggle-group"

const uriRegex = new RegExp('^(https?:\/\/)(localhost|[\da-z\.-]+)\.([a-z\.]{2,6}|[0-9]{1,5})([\/\w \.-]*)*\/?$');

const decimalRegex = /^-?\d+(\.\d)?$/;

const formSchema = z.object({
  amenities: z.array(z.string().max(255)),
  title: z.string().max(255),
  address: z.string().max(255),
  beds: z.preprocess((value) => {
    // If value is already a number, return it
    if (typeof value === 'number') return value;
    // If it's a string, attempt to parse it
    if (typeof value === 'string') return parseFloat(value);
  }, z.number().int().min(0).max(2147483647)),
  baths: z.union([
    z.string().regex(decimalRegex).optional().transform((val) => val !== undefined ? parseFloat(val) : undefined),
    z.number().min(0).max(100).optional()
  ]).refine((val) => val === undefined || (typeof val === 'number' && val >= 0 && val <= 100 && decimalRegex.test(val.toString())), {
    message: "Baths must be a decimal with at most one decimal place and within the range -100 to 100."
  }),
  description: z.string().optional(),
  external_link: z.string().regex(uriRegex).max(255),
  price: z.preprocess((value) => {
    // If value is already a number, return it
    if (typeof value === 'number') return value;
    // If it's a string, attempt to parse it
    if (typeof value === 'string') return parseFloat(value);
  }, z.number().int().min(-2147483648).max(2147483647)),
  negotiable: z.boolean().optional(),
  start_date: z.date(),
  end_date: z.date(),
  expires_at: z.date(),
  //start_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  //end_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  //expires_at: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/),
});

interface PropertyFormProps {
  children: React.ReactNode;
}

const PropertyForm = ({ children }: PropertyFormProps) => {

  //const { toast } = useToast();
  const [amenities, setAmenities] = useState<string[]>([]);

  useEffect(() => {
    fetchAmenities()
      .then((data) => {
        setAmenities(data);
      })
      .catch((error) => {
        console.error("Error fetching properties:", error);
      });
  }, []);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      amenities: [],
      title: "",
      address: "",
      beds: 0,
      baths: 0,
      description: "",
      external_link: "",
      price: 0,
      negotiable: false,
      start_date: undefined,
      end_date: undefined,
      expires_at: undefined,
    },
  })

  function onSubmit(values: z.infer<typeof formSchema>) {
    const property = {
      ...values,
      start_date: format(values.start_date, "yyyy-MM-dd") as string,
      end_date: format(values.end_date, "yyyy-MM-dd") as string,
      expires_at: format(values.expires_at, "yyyy-MM-dd") as string,
      baths: values.baths!.toString(),
    };

    console.log(JSON.stringify(property));

    createProperty(property)
      .then((data) => {
        console.log("Property created:", data);
      })
      .catch((error) => {
        console.error("Error fetching properties:", error);
      });
  }

  return (
    <div>
      <Sheet>
        <SheetTrigger asChild>
          {children}
        </SheetTrigger>
        <SheetContent className="space-y-4 overflow-y-scroll">
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
                  <FormItem className="grid grid-cols-4 items-center gap-1  pt-5">
                    <FormLabel htmlFor="title" className="text-right pr-3">Name</FormLabel>
                    <FormControl className="col-span-3">
                      <Input placeholder="ex. Chestnut 2bed 2ba" {...field} />
                    </FormControl>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="address"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1">
                    <FormLabel htmlFor="address" className="text-right pr-3">Address</FormLabel>
                    <FormControl className="col-span-3">
                      <Input type="string" placeholder="123 Main St, Philadelphia, PA 19104" {...field} />
                    </FormControl>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="price"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1">
                    <FormLabel htmlFor="price" className="text-right pr-3">Price</FormLabel>
                    <FormControl className="col-span-3">
                      <Input type="number" {...field} />
                    </FormControl>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="negotiable"
                render={({ field }) => (
                  <FormItem className="flex justify-end items-center gap-1">
                    <div className="flex gap-2">
                      <FormControl className="">
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                      <FormLabel htmlFor="negotiable" className="text-right col-start-3">
                        Negotiable?
                      </FormLabel>
                    </div>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="external_link"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1">
                    <FormLabel htmlFor="external_link" className="text-right pr-3">Link</FormLabel>
                    <FormControl className="col-span-3">
                      <Input placeholder="https://example.com" {...field} />
                    </FormControl>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-2 items-center gap-1 justify-start items-start pb-5">
                <FormField
                  control={form.control}
                  name="beds"
                  render={({ field }) => (
                    <FormItem className="grid grid-cols-2 items-center gap-1">
                      <FormLabel htmlFor="beds" className="text-right pr-3">Beds</FormLabel>
                      <FormControl className="col-span-1">
                        <Input type="number" {...field} />
                      </FormControl>

                      {/*<FormMessage className="col-span-4 text-right" />*/}
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="baths"
                  render={({ field }) => (
                    <FormItem className="grid grid-cols-2 items-center  gap-1">
                      <FormLabel htmlFor="baths" className="text-right pr-3">Baths</FormLabel>
                      <FormControl className="col-span-1">
                        <Input type="number" {...field} />
                      </FormControl>

                      {/*<FormMessage className="col-span-4 text-right" />*/}
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="start_date"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1">
                    <FormLabel htmlFor="start_date" className="text-right pr-3">Start Date</FormLabel>
                    <Popover>
                      <PopoverTrigger asChild className="">
                        <FormControl className="col-span-3">
                          <Button
                            variant={"outline"}
                            className={cn(
                              "pl-3 text-left font-normal",
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
                            date < new Date() || date > form.getValues("end_date")!
                          }
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="end_date"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1">
                    <FormLabel htmlFor="end_date" className="text-right pr-3">End Date</FormLabel>
                    <Popover>
                      <PopoverTrigger asChild>
                        <FormControl className="col-span-3">
                          <Button
                            variant={"outline"}
                            className={cn(
                              "pl-3 text-left font-normal",
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
                            (form.getValues("start_date") ? date < new Date(form.getValues("start_date")) : date < new Date()) || date < form.getValues("expires_at")
                          }
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="expires_at"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1 pb-5">
                    <FormLabel htmlFor="expires_at" className="text-right pr-3">Expires At</FormLabel>
                    <Popover>
                      <PopoverTrigger asChild className="">
                        <FormControl className="col-span-3">
                          <Button
                            variant={"outline"}
                            className={cn(
                              "pl-3 text-left font-normal",
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
                            date < new Date() || date > form.getValues("end_date")
                          }
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="amenities"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1 pb-5">
                    <FormLabel htmlFor="amenities" className="text-right pr-3">Amenities</FormLabel>
                    <FormControl className="col-span-3">
                      <ToggleGroup
                        type="multiple"
                        className="flex flex-wrap justify-start gap-2"
                      >
                        {amenities.map((amenity, id) => (
                          <ToggleGroupItem
                            key={id}
                            value={amenity}
                            data-state={field.value?.includes(amenity) ? "on" : "off"}
                            aria-label="Toggle bold"
                            className="border"
                            onClick={() => {
                              const currentAmenities = field.value || [];
                              const updatedAmenities = currentAmenities.includes(amenity)
                                ? currentAmenities.filter(a => a !== amenity)  // Remove the amenity if it was selected
                                : [...currentAmenities, amenity];  // Add the amenity if it was not selected

                              field.onChange(updatedAmenities);  // Update the form field's value
                            }}
                          >
                            <Label className="p-0">
                              {amenity}
                            </Label>
                          </ToggleGroupItem>
                        ))}
                      </ToggleGroup>
                    </FormControl>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem className="grid grid-cols-4 items-center gap-1">
                    <FormLabel htmlFor="description" className="text-right pr-3">Description</FormLabel>
                    <FormControl className="col-span-3">
                      <Textarea placeholder="Add features or descriptors..." {...field} />
                    </FormControl>
                    <FormMessage className="col-span-4 text-right" />
                  </FormItem>
                )}
              />

              {/*<Button onClick={() => {
                console.log(form.getValues())
                //console.log("Start Date:", format(form.getValues("start_date"), "yyyy-MM-dd"));
                //console.log("End Date:", format(form.getValues("end_date"), "yyyy-MM-dd"));
                console.log(form.getFieldState("external_link"))
                //console.log(form.getFieldState("end_date"))
              }}>
                console log
            </Button>*/}

              <SheetFooter className="max-sm:flex max-sm: max-sm:gap-2 py-5">
                <SheetClose asChild>
                  <Button variant="secondary">Close</Button>
                </SheetClose>
                <Button type="submit">Save</Button>
              </SheetFooter>

            </form>
          </Form>
        </SheetContent>
      </Sheet >
    </div >
  )
}

export default PropertyForm