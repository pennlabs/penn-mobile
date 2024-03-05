"use client";

import { useState, useEffect } from "react";

import { fetchProperties } from "../../services/propertyService";
import { PropertyInterface } from "@/interfaces/Property";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { Button } from "@/components/ui/button";

import { PlusIcon } from "@radix-ui/react-icons";

import PropertyList from "@/components/custom/PropertyList";

import PropertyForm from "@/components/custom/PropertyForm";

const Dashboard = () => {
  const [properties, setProperties] = useState<PropertyInterface[]>([]);

  useEffect(() => {
    fetchProperties()
      .then((data) => {
        setProperties(data);
      })
      .catch((error) => {
        console.error("Error fetching properties:", error);
      });
  }, []);

  return (
    <div className="">
      <Tabs defaultValue="posted" className="">

        <div className="w-screen flex justify-end p-6 gap-4">
          <TabsList>
            <TabsTrigger value="posted">Posted</TabsTrigger>
            <TabsTrigger value="drafts">Drafts</TabsTrigger>
          </TabsList>
          <PropertyForm>
            <Button className="p-2">
              <PlusIcon className="w-5" />
            </Button>
          </PropertyForm>
        </div>


        <TabsContent value="posted" className="p-14">
          <div className="flex flex-col justify-center space-y-12">
            <h1 className="text-4xl tracking-tight font-bold">
              Your Listings
            </h1>
            <PropertyList properties={properties} />
          </div>
        </TabsContent>


        <TabsContent value="drafts" className="p-6">
          <div className="pl-20 space-y-10">
            <h1 className="text-4xl tracking-tighter font-semibold">
              Dashboard
            </h1>
            <PropertyList properties={properties} />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Dashboard;
